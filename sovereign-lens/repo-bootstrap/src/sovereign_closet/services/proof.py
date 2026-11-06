from sovereign_closet.domain.proof_job import ProofJob
from sovereign_closet.config import settings

def create_proof_job(job: ProofJob) -> ProofJob:
    if settings.proof_jobs_billable:
        return job
    job.billable = False
    job.provider = None
    job.status = "validated_non_billable"
    return job
