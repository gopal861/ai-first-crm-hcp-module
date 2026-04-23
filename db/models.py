from sqlalchemy import Column, Integer, String, Text
from db.database import Base


class Interaction(Base):
    __tablename__ = "interactions" 
    __table_args__ = {"schema": "public"} 

    id = Column(Integer, primary_key=True, index=True)
    hcp_name = Column(String)
    interaction_type = Column(String)
    date = Column(String)
    time = Column(String)
    attendees = Column(Text)
    discussion_topics = Column(Text)
    materials_shared = Column(Text)
    samples_distributed = Column(Text)
    sentiment = Column(String)
    outcomes = Column(Text)
    follow_up_actions = Column(Text)