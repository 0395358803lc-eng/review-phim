# narrative.json — Event and Causal Graph

## Envelope bắt buộc cho mọi artifact
schema_version: string (mặc định "1.0"); job_id: string; source_sha256: string (64 ký tự hex của tệp nguồn); generator: object {name:string,version:string, config_hash:string}; produced_at: ISO-8601 UTC string. Hash của artifact được lưu trong stage manifest; dữ liệu không chứa credentials.

## Fields
- events: {event_id,scene_ids,character_ids,description,state,evidence_ids,screen_time_s,story_order?}[]
- edges: {edge_id,from_event_id,to_event_id,relation(BEFORE|CAUSES|MOTIVATES|REVEALS|CONTRADICTS),state,evidence_ids}[]
- entities: {entity_id,labels,identity_state,evidence_ids}[]
- unresolved: array of {question,needed_evidence_ids?,impact}

## Example synthetic (KHÔNG phải kết quả phân tích video thật)
~~~json
{
  "schema_version": "1.0",
  "job_id": "DEMO-001",
  "source_sha256": "0000000000000000000000000000000000000000000000000000000000000000",
  "generator": {
    "name": "synthetic-fixture",
    "version": "0",
    "config_hash": "demo"
  },
  "produced_at": "2026-10-30T00:00:00Z",
  "events": [
    {
      "event_id": "EVENT_01",
      "scene_ids": [
        "SC_042"
      ],
      "character_ids": [
        "CHAR_01"
      ],
      "description": "radio emits warning",
      "state": "INFERRED",
      "evidence_ids": [
        "EV_042"
      ],
      "screen_time_s": 3124.2,
      "story_order": null
    }
  ],
  "edges": [],
  "entities": [
    {
      "entity_id": "CHAR_01",
      "labels": [
        "Mara?"
      ],
      "identity_state": "INFERRED",
      "evidence_ids": [
        "EV_042"
      ]
    }
  ],
  "unresolved": [
    {
      "question": "Who speaks over the radio?",
      "impact": "critical plot identification"
    }
  ]
}
~~~

## Validation checks
- No dangling event/entity/evidence IDs
- Cause or motive not inferred from screen-order adjacency
- Nonlinear story can carry independent screen-time and story-order

Tham khảo ORCHESTRATION.md: schema invalid -> stage FAIL/NOT_TESTED, không được tự động coi là PASS.
