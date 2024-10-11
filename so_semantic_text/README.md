## StackOverflow semantic_text track

This track is based on the excellent work of @Mikep86
 [here](https://github.com/Mikep86/rally-tracks/tree/mikep86/semantic-text-so-track/so_semantic_text).

This rally track assumes there will be an alias `so-semantic-text` on the targeted ES3 project.

There are 3 challenges:
1. `index` - it will rollover the alias, index 1 documents into the alias, and delete all the non-write-indices.
2. `random-update` - it will randomly select some documents and update the `title` field randomly.
3. `semantic-search` - it will benchmark the semantic_text search.

The corpus is the same as that used by the `so` track; see `so/README.md` for more info about it.

### Generating the query set

Since the `so` track does not include queries, they were synthetically generated for this track
using the titles of questions from the corpus.
Only the first 1,000,000 questions were used to keep the query file size manageable.

To regenerate the query set from scratch, download the `so` corpus using
[this link](https://rally-tracks.elastic.co/so/posts.json.bz2) and run the query generation script:

```shell
./_tools/generate_queries.py -c 1000000 <path_to_posts_file> queries.txt.bz2
```

### Parameters

This track allows to overwrite the following parameters with Rally 0.8.0+ using `--track-params`:

* `bulk_size` (default: 10)
* `bulk_indexing_clients` (default: 8): Number of clients that issue bulk indexing requests.
* `ingest_percentage` (default: 100): A number between 0 and 100 that defines how much of the document corpus should be ingested.
* `error_level` (default: "non-fatal"): Available for bulk operations only to specify ignore-response-error-level.
* `random_update_percentage` (default: 5): A number between 0 and 100 that defines how much of the document corpus should be updated.
* `random_update_bulk_size` (default: 100): The bulk size for bulk update operation.
* `semantic_search_clients` (default: 1): The number of clients that issue queries in the `semantic-search` operation.
* `semantic_search_time_period` (default: 300): The time period, in seconds, to execute the `semantic-search` operation for.
* `semantic_search_warmup_time_period` (default: 10): The warmup time period, in seconds, for the `semantic-search` operation.
* `semantic_search_page_size` (default: 20): The number of results to fetch for each query.
* `semantic_search_target_throughput` (default: 1): The target throughput of the `semantic-search` operation.

### License

We use the same license for the data as the original data: [CC-SA-3.0](http://creativecommons.org/licenses/by-sa/3.0/)


