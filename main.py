from enum import Enum
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Campaign Management API")


class CampaignStatus(str, Enum):
    idea = "idea"
    drafted = "drafted"
    designed = "designed"
    reviewed = "reviewed"
    approved = "approved"
    scheduled = "scheduled"
    published = "published"
    archived = "archived"


class CampaignCreate(BaseModel):
    name: str
    aura: str


class StateUpdate(BaseModel):
    status: CampaignStatus


class Campaign(BaseModel):
    id: str
    name: str
    aura: str
    status: CampaignStatus


# In-memory store
campaigns: dict[str, Campaign] = {}


@app.post("/campaigns", response_model=Campaign, status_code=201)
def create_campaign(payload: CampaignCreate) -> Campaign:
    campaign = Campaign(
        id=str(uuid4()),
        name=payload.name,
        aura=payload.aura,
        status=CampaignStatus.idea,
    )
    campaigns[campaign.id] = campaign
    return campaign


@app.get("/campaigns", response_model=list[Campaign])
def list_campaigns() -> list[Campaign]:
    return list(campaigns.values())


@app.patch("/campaigns/{campaign_id}/state", response_model=Campaign)
def update_campaign_state(campaign_id: str, payload: StateUpdate) -> Campaign:
    campaign = campaigns.get(campaign_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    updated = campaign.model_copy(update={"status": payload.status})
    campaigns[campaign_id] = updated
    return updated
