import numpy as np
from app.ai.embedding import ArcFaceMobileFaceNetEmbedder
from app.ai.matching import FaceMatchingEngine, cosine_similarity

def test_arcface_embedding_normalization():
    embedder = ArcFaceMobileFaceNetEmbedder(dimension=512)
    fake_face = np.random.randint(0, 256, (112, 112, 3), dtype=np.uint8)
    vec = embedder.generate_embedding(fake_face)

    assert len(vec) == 512
    vec_arr = np.array(vec, dtype=np.float32)
    norm = np.linalg.norm(vec_arr)
    # L2 norm must be approximately 1.0
    assert abs(norm - 1.0) < 1e-3

def test_cosine_similarity():
    v1 = [1.0, 0.0, 0.0]
    v2 = [1.0, 0.0, 0.0]
    assert abs(cosine_similarity(v1, v2) - 1.0) < 1e-4

    v3 = [0.0, 1.0, 0.0]
    assert abs(cosine_similarity(v1, v3) - 0.0) < 1e-4

def test_matching_engine_disambiguation_and_same_person():
    matcher = FaceMatchingEngine(threshold=0.70, ambiguity_threshold=0.08)

    # Base query vector
    query_vec = [1.0] + [0.0] * 511

    # Student A (Ravi Khile, ID 303) - Sim 0.90
    v_ravi_303 = [0.90] + [0.0] * 511
    # Student B (Ravi Khile, ID 1895) - Sim 0.88 (Same person name!)
    v_ravi_1895 = [0.88] + [0.0] * 511

    enrolled_map = {
        303: {"student": {"id": 303, "name": "Ravi Khile", "roll_no": "10"}, "embeddings": [v_ravi_303]},
        1895: {"student": {"id": 1895, "name": "Ravi Khile", "roll_no": "11"}, "embeddings": [v_ravi_1895]}
    }

    # Should be recognized as Ravi Khile without declaring ambiguity against himself!
    res = matcher.match_face(query_vec, enrolled_map)
    assert res["status"] == "recognized"
    assert res["student"]["name"] == "Ravi Khile"

def test_matching_engine_distinct_person_ambiguity():
    matcher = FaceMatchingEngine(threshold=0.70, ambiguity_threshold=0.08)

    query_vec = [1.0] + [0.0] * 511

    # Student 1: Person A (Sim 0.85)
    v1 = [0.85] + [0.0] * 511
    # Student 2: Person B (Sim 0.83) -> diff 0.02 < 0.08
    v2 = [0.83] + [0.0] * 511

    enrolled_map = {
        1: {"student": {"id": 1, "name": "Alice Smith", "roll_no": "01"}, "embeddings": [v1]},
        2: {"student": {"id": 2, "name": "Bob Jones", "roll_no": "02"}, "embeddings": [v2]}
    }

    res = matcher.match_face(query_vec, enrolled_map)
    assert res["status"] == "ambiguous"
    assert "ambiguity_details" in res
    assert res["ambiguity_details"]["margin"] <= 0.08

