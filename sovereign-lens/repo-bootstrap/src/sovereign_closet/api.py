from fastapi import FastAPI
from sovereign_closet.domain.style_brief import StyleBrief
from sovereign_closet.domain.proof_job import ProofJob
from sovereign_closet.repositories.products import SEED_PRODUCTS
from sovereign_closet.services.composer import compose_outfits
from sovereign_closet.services.proof import create_proof_job

app = FastAPI(title="Sovereign Closet", version="0.1.0")

@app.get("/health")
def health():
    return {"status": "ok", "service": "sovereign-closet"}

@app.post("/api/outfits/generate")
def generate_outfits(brief: StyleBrief):
    looks = compose_outfits(SEED_PRODUCTS, brief, limit=10)
    return {"count": len(looks), "looks": [x.model_dump() for x in looks]}

@app.post("/api/proof-jobs")
def proof_job(job: ProofJob):
    return create_proof_job(job).model_dump()
