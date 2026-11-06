from sovereign_closet.domain.proof_job import ProofJob
from sovereign_closet.canon.progression import ProgressionLevel
from sovereign_closet.services.proof import create_proof_job

def test_proof_jobs_are_non_billable():
    job = ProofJob(outfit_id="look-1", progression_level=ProgressionLevel.NORTH_STAR)
    result = create_proof_job(job)
    assert result.billable is False
    assert result.provider is None
    assert result.status == "validated_non_billable"
