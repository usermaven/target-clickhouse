from clickhouse_sqlalchemy import engines

ENGINE_MAPPING = {
    "MergeTree": engines.MergeTree,
    "ReplacingMergeTree": engines.ReplacingMergeTree,
    "SummingMergeTree": engines.SummingMergeTree,
    "AggregatingMergeTree": engines.AggregatingMergeTree,
    "ReplicatedMergeTree": engines.ReplicatedMergeTree,
    "ReplicatedReplacingMergeTree": engines.ReplicatedReplacingMergeTree,
    "ReplicatedSummingMergeTree": engines.ReplicatedSummingMergeTree,
    "ReplicatedAggregatingMergeTree": engines.ReplicatedAggregatingMergeTree,
}


def get_engine_class(engine_type):
    return ENGINE_MAPPING.get(engine_type)
