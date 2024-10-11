import bz2
import copy
import logging
from os.path import dirname
import random

from datetime import datetime, timezone, timedelta
from elasticsearch.helpers import async_scan
from esrally.track.params import ParamSource

QUERIES_DIRNAME: str = dirname(__file__)
QUERIES_FILENAME: str = f"{QUERIES_DIRNAME}/queries.txt.bz2"
INDEX = "so-semantic-text"

logger = logging.getLogger(__name__)


class SemanticSearchParamSource(ParamSource):
    def __init__(self, track, params, **kwargs):
        super().__init__(track, params, **kwargs)
        self._queries = self._read_queries()

    @staticmethod
    def _read_queries():
        queries = []
        with bz2.open(QUERIES_FILENAME, mode="r") as queries_file:
            for query in queries_file:
                query = query.decode("utf-8")
                escaped_query = query.replace("\"", "\\\"").strip()
                queries.append(escaped_query)

        return queries

    def params(self):
        query = random.choice(self._queries)
        es_query = {
            "semantic": {
                "field": "title_semantic",
                "query": query
            }
        }

        return {
            "body": {
                "query": es_query
            },
            "size": self._params["size"],
            "index": INDEX
        }


class DeleteOldIndicesRunner:
    async def __call__(self, es, params):
        # delete all non-write indices
        alias = await es.indices.get(index=INDEX)
        indices_to_delete = []
        for index in alias:
            if not alias.get(index).get("aliases", {}).get(INDEX, {}).get("is_write_index", True):
                indices_to_delete.append(index)

        if not indices_to_delete:
            logger.info("There's no old indices to delete")
            return

        indices_to_delete = ",".join(indices_to_delete)
        logger.info(f"Delete old indices {indices_to_delete}")
        await es.indices.delete(index=indices_to_delete)

    def __repr__(self, *args, **kwargs):
        return "delete-old-indices"


class RandomUpdateRunner:
    async def __call__(self, es, params):
        update_percentage = min(100, max(0, params["update-percentage"]))
        if update_percentage == 0:
            logger.info(f"No documents will be updated as the param update-percentage is {update_percentage}")
            return

        alias = await es.indices.get(index=INDEX)
        write_index = None
        for index in alias:
            if alias.get(index).get("aliases", {}).get(INDEX, {}).get("is_write_index", False):
                write_index = index
                break

        if not write_index:
            logger.error(f"Couldn't find write index for alias {INDEX}, skip random update.")
            return

        # calculate the number of documents to update
        resp = await es.count(index=write_index, ignore_unavailable=True)
        update_target = int(resp["count"] * update_percentage / 100)
        logger.info(f"Randomly select {update_percentage / 100:.0%} of documents ({update_target:,}) to update.")

        queries = self._read_queries()
        # randomly select some documents to update
        query = {
            "query": {
                "function_score": {
                    "functions": [
                        {
                            "random_score": {
                                "seed": int(datetime.now().timestamp()),
                                "field": "questionId"
                            }
                        }
                    ]
                }
            }
        }
        bulk_payload = []
        bulk_size = params["bulk-size"]
        count = 0
        async for doc in async_scan(client=es, index=write_index, query=query, _source=False):
            bulk_payload.append({"update": {"_index": write_index, "_id": doc["_id"]}})
            random_query = random.choice(queries)
            bulk_payload.append({"doc": {"title": random_query, "title_semantic": random_query}})
            count += 1
            if len(bulk_payload) / 2 >= bulk_size:
                await es.bulk(operations=copy.copy(bulk_payload))
                bulk_payload.clear()

            if count >= update_target:
                break

        if bulk_payload:
            await es.bulk(operations=copy.copy(bulk_payload))

    @staticmethod
    def _read_queries():
        queries = []
        with bz2.open(QUERIES_FILENAME, mode="r") as queries_file:
            for query in queries_file:
                query = query.decode("utf-8")
                escaped_query = query.replace("\"", "\\\"").strip()
                queries.append(escaped_query)

        return queries

    def __repr__(self, *args, **kwargs):
        return "random_update"


def register(registry):
    registry.register_param_source("semantic-search-param-source", SemanticSearchParamSource)
    registry.register_runner("delete-old-indices", DeleteOldIndicesRunner(), async_runner=True)
    registry.register_runner("random-update", RandomUpdateRunner(), async_runner=True)
