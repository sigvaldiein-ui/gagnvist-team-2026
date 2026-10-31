"""API-level planner recovery and service-only stopping, using synthetic facts."""

import importlib.util
import io
import json
from pathlib import Path

import httpx
import numpy as np
import pytest
import standin
from test_grounded_answer import ENTRY, fact
from test_model_client import chat_reply, client_answering

from gagnvist.answering.grounded_answer import (
    PLAN_SCHEMA,
    cell_references,
    grounded_answer,
    period_mode,
    validate_calculation_plan,
)
from gagnvist.answering.pipeline import Pipeline
from gagnvist.models.client import ModelContentError, ModelError
from gagnvist.search.table_index import TableIndex
from gagnvist.search.vector_search import Card, VectorIndex


@pytest.mark.parametrize(
    "reply",
    [
        "[]",
        "{}",
        "{broken",
        "",
        '{"operation":"ratio"}',
        '{"operation":"ratio","operands":[]}',
        '{"operation":"ratio","operands":[0,99]}',
        '{"operation":"ratio","operands":[-1,0]}',
        '{"operation":"ratio","operands":[false,1]}',
        '{"operation":"ratio","operands":[0.0,1]}',
        '{"operation":"ratio","operands":[0,0]}',
        '{"operation":"invented","operands":[0]}',
        '{"operation":"none","operands":[0],"value":999}',
    ],
)
def test_bad_planner_payload_falls_back_through_real_client(reply: str) -> None:
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        calls.append(body)
        return chat_reply(reply if "response_format" in body else "Published: 150 and 120.")

    facts = [fact("2018", "T", 150), fact("2017", "T", 120)]
    client = client_answering(handler)
    result = grounded_answer("A comparison?", "en", ENTRY, facts, client)
    client.close()
    assert result.text == "Published: 150 and 120."
    assert result.notes[0].startswith("plan_fallback:")
    assert result.validated_numbers == []
    assert result.cell_references == cell_references(ENTRY, facts)
    assert result.period_mode == period_mode(facts)
    assert len(calls) == 2
    assert calls[0]["response_format"]["json_schema"]["schema"] == PLAN_SCHEMA


@pytest.mark.parametrize(
    "proposal", [[], {}, None, {"operation": "none"}, {"operation": "none", "operands": [True]}]
)
def test_code_validation_does_not_trust_server(proposal: object) -> None:
    with pytest.raises(ValueError):
        validate_calculation_plan(proposal, 2)


@pytest.mark.parametrize("denominator", [0.0, 1e-13, -1e-13])
def test_zero_and_near_zero_denom_use_fact_writer(denominator: float) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        return chat_reply(
            '{"operation":"pct_change","operands":[0,1]}'
            if "response_format" in body
            else "Published values only."
        )

    client = client_answering(handler)
    result = grounded_answer(
        "Change?", "en", ENTRY, [fact("2018", "T", 150), fact("2017", "T", denominator)], client
    )
    client.close()
    assert result.text == "Published values only."
    assert "denominator" in result.notes[0]
    assert result.calculations[0]["status"] == "rejected"
    assert not result.validated_numbers


def test_valid_arithmetic_uses_indices_not_model_values() -> None:
    client = client_answering(
        lambda request: chat_reply('{"operation":"pct_change","operands":[0,1]}')
    )
    result = grounded_answer(
        "Change?", "en", ENTRY, [fact("2018", "T", 150), fact("2017", "T", 120)], client
    )
    client.close()
    assert result.calculations[0]["displayed"] == "25"
    assert result.calculations[0]["cell_references"] == ["cell-aa", "cell-ab"]
    assert not result.notes


@pytest.mark.parametrize("failure", ["http500", "connect", "timeout", "fallback_http500"])
def test_service_errors_are_never_swallowed(failure: str) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if failure == "connect":
            raise httpx.ConnectError("offline", request=request)
        if failure == "timeout":
            raise httpx.ReadTimeout("timeout", request=request)
        if failure == "fallback_http500" and "response_format" in json.loads(request.content):
            return chat_reply("[]")
        return httpx.Response(500, json={"error": "service unavailable"})

    client = client_answering(handler)
    with pytest.raises(ModelError) as caught:
        grounded_answer("Question?", "en", ENTRY, [fact("2018", "T", 150)], client)
    client.close()
    assert not isinstance(caught.value, ModelContentError)


def test_bad_factual_writer_payload_preserves_raw_facts() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if "response_format" in json.loads(request.content):
            return chat_reply("[]")
        return httpx.Response(200, json={"choices": [{"message": {"content": None}}]})

    client = client_answering(handler)
    result = grounded_answer("Question?", "en", ENTRY, [fact("2018", "T", 150)], client)
    client.close()
    assert "150" in result.text and result.notes[1].startswith("fact_fallback:")


def test_pipeline_survives_non_object_planner_json(data_folder: Path, table_database: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        schema = body.get("response_format", {}).get("json_schema", {}).get("schema", {})
        if "operation" in schema.get("properties", {}):
            return chat_reply("[]")
        return standin.handle(request)

    client = client_answering(handler)
    folder = "Economy/en/visitolur/2_byggingarvisitala/byggingarvisitala/VIS13401"
    vectors = VectorIndex(
        [Card(folder, "en", "Construction cost index")],
        np.ones((1, standin.DIMENSIONS), dtype=np.float32),
        standin.EMBEDDING_MODEL,
    )
    with Pipeline(data_folder, TableIndex(table_database), vectors, client) as pipeline:
        answer = pipeline.answer("Construction cost index in 2025", language="en")
    assert answer.text.startswith("Stand-in answer:")
    assert any(n.startswith("plan_fallback:") for n in answer.notes)
    assert answer.cell_references and answer.unsupported == []


@pytest.mark.parametrize("failure,kind", [("[]", "content"), ("http500", "service")])
def test_measurement_records_failure_and_stops_only_on_service(failure: str, kind: str) -> None:
    path = Path(__file__).parents[1] / "tools/measure_5b3.py"
    spec = importlib.util.spec_from_file_location("measurement", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    client = client_answering(
        lambda request: httpx.Response(500) if failure == "http500" else chat_reply(failure)
    )
    trace = io.StringIO()
    recorder = module.RecordingClient(client, trace)
    with pytest.raises(ModelError):
        recorder.chat_json([{"role": "user", "content": "Synthetic"}], PLAN_SCHEMA)
    recorder.close()
    recorded = json.loads(trace.getvalue())
    assert recorded["error_kind"] == kind
    assert bool(recorder.service_error) == (kind == "service")
