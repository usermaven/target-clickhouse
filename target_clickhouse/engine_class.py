from clickhouse_sqlalchemy import engines

ENGINE_MAPPING = {
    "MergeTree": engines.MergeTree,
    "ReplacingMergeTree": engines.ReplacingMergeTree,
    "SummingMergeTree": engines.SummingMergeTree,
    "CollapsingMergeTree": engines.CollapsingMergeTree,
    "VersionedCollapsingMergeTree": engines.VersionedCollapsingMergeTree,
    "AggregatingMergeTree": engines.AggregatingMergeTree,
    "GraphiteMergeTree": engines.GraphiteMergeTree,
    "ReplicatedMergeTree": engines.ReplicatedMergeTree,
    "ReplicatedSummingMergeTree": engines.ReplicatedSummingMergeTree,
    "ReplicatedCollapsingMergeTree": engines.ReplicatedCollapsingMergeTree,
    "ReplicatedReplacingMergeTree": engines.ReplicatedReplacingMergeTree,
    "ReplicatedAggregatingMergeTree": engines.ReplicatedAggregatingMergeTree,
    "ReplicatedVersionedCollapsingMergeTree": engines.ReplicatedVersionedCollapsingMergeTree,
}


def get_engine_class(engine_type):
    return ENGINE_MAPPING.get(engine_type)
