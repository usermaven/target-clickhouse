from __future__ import annotations

import typing
from typing import TYPE_CHECKING

import sqlalchemy.types
from clickhouse_sqlalchemy import (
    Table,
)
from singer_sdk import typing as th
from singer_sdk.connectors import SQLConnector
from sqlalchemy import Column, MetaData, create_engine

from target_clickhouse.engine_class import get_engine_class

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine

class ClickhouseConnector(SQLConnector):
    """Clickhouse Meltano Connector.

    Inherits from `SQLConnector` class, overriding methods where needed
    for Clickhouse compatibility.
    """

    allow_column_add: bool = True  # Whether ADD COLUMN is supported.
    allow_column_rename: bool = True  # Whether RENAME COLUMN is supported.
    allow_column_alter: bool = True  # Whether altering column types is supported.
    allow_merge_upsert: bool = False  # Whether MERGE UPSERT is supported.
    allow_temp_tables: bool = True  # Whether temp tables are supported.

    def get_sqlalchemy_url(self, config: dict) -> str:
        """Generates a SQLAlchemy URL for clickhouse.

        Args:
            config: The configuration for the connector.
        """
        return super().get_sqlalchemy_url(config)

    def create_engine(self) -> Engine:
        """Create a SQLAlchemy engine for clickhouse."""
        return create_engine(self.get_sqlalchemy_url(self.config))

    def to_sql_type(self, jsonschema_type: dict) -> sqlalchemy.types.TypeEngine:
        """Return a JSON Schema representation of the provided type.

        Developers may override this method to accept additional input argument types,
        to support non-standard types, or to provide custom typing logic.

        Args:
            jsonschema_type: The JSON Schema representation of the source type.

        Returns:
            The SQLAlchemy type representation of the data type.
        """
        sql_type = th.to_sql_type(jsonschema_type)

        # Clickhouse does not support the DECIMAL type without providing precision,
        # so we need to use the FLOAT type.
        if type(sql_type) == sqlalchemy.types.DECIMAL:
            sql_type = typing.cast(
                sqlalchemy.types.TypeEngine, sqlalchemy.types.FLOAT(),
            )

        return sql_type

    def create_empty_table(
        self,
        full_table_name: str,
        schema: dict,
        primary_keys: list[str] | None = None,
        partition_keys: list[str] | None = None,
        as_temp_table: bool = False,  # noqa: FBT001, FBT002
        engine_type: str = "MergeTree",  # Default to MergeTree engine
        table_path: str | None = None,
        replica_name: str | None = None,
        cluster_name: str | None = None,
    ) -> None:
        """Create an empty target table, using Clickhouse Engine.

        Args:
            full_table_name: the target table name.
            schema: the JSON schema for the new table.
            primary_keys: list of key properties.
            partition_keys: list of partition keys.
            as_temp_table: True to create a temp table.
            engine_type: Clickhouse engine type.
            table_path: table path for replicated tables .eg. '/clickhouse/tables/{uuid}/{shard}',
            replica_name: replica name for replicated tables.
            cluster_name: cluster name for replicated tables.

        Raises:
            NotImplementedError: if temp tables are unsupported and as_temp_table=True.
            RuntimeError: if a variant schema is passed with no properties defined.
        """
        if as_temp_table:
            msg = "Temporary tables are not supported."
            raise NotImplementedError(msg)

        _ = partition_keys  # Not supported in generic implementation.

        _, _, table_name = self.parse_full_table_name(full_table_name)

        # If config table name is set, then use it instead of the table name.
        if self.config.get("table_name"):
            table_name = self.config.get("table_name")

        # Do not set schema, as it is not supported by Clickhouse.
        meta = MetaData(schema=None, bind=self._engine)
        columns: list[Column] = []
        primary_keys = primary_keys or []
        try:
            properties: dict = schema["properties"]
        except KeyError as e:
            msg = f"Schema for '{full_table_name}' does not define properties: {schema}"
            raise RuntimeError(msg) from e
        for property_name, property_jsonschema in properties.items():
            is_primary_key = property_name in primary_keys
            columns.append(
                Column(
                    property_name,
                    self.to_sql_type(property_jsonschema),
                    primary_key=is_primary_key,
                ),
            )

        engine_class = get_engine_class(engine_type)
        if engine_class is None:
            raise ValueError(f"Unsupported engine type: {engine_type}")
        
        engine_args = {"primary_key": primary_keys}
        if table_path is not None:
            engine_args["table_path"] = table_path
        if replica_name is not None:
            engine_args["replica_name"] = replica_name

        table_args = {}
        if cluster_name is not None:
            table_args["clickhouse_cluster"] = cluster_name

        table_engine = engine_class(**engine_args)
        _ = Table(table_name, meta, *columns, table_engine, **table_args)
        meta.create_all(self._engine)

    def prepare_schema(self, _: str) -> None:
        """Create the target database schema.

        In Clickhouse, a schema is a database, so this method is a no-op.

        Args:
            schema_name: The target schema name.
        """
        return

    @staticmethod
    def get_column_alter_ddl(
        table_name: str,
        column_name: str,
        column_type: sqlalchemy.types.TypeEngine,
    ) -> sqlalchemy.DDL:
        """Get the alter column DDL statement.

        Override this if your database uses a different syntax for altering columns.

        Args:
            table_name: Fully qualified table name of column to alter.
            column_name: Column name to alter.
            column_type: New column type string.

        Returns:
            A sqlalchemy DDL instance.
        """
        return sqlalchemy.DDL(
            "ALTER TABLE %(table_name)s MODIFY COLUMN %(column_name)s %(column_type)s",
            {
                "table_name": table_name,
                "column_name": column_name,
                "column_type": column_type,
            },
        )
