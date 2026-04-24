import hashlib
import json
from datetime import datetime

def calculate_hash(index, candidate_id, election_id, timestamp, previous_hash):
    """
    Calculates the SHA-256 hash of a vote block.
    """
    if isinstance(timestamp, datetime):
        timestamp = timestamp.isoformat()
        
    block_string = json.dumps({
        "index": index,
        "candidate_id": candidate_id,
        "election_id": election_id,
        "timestamp": timestamp,
        "previous_hash": previous_hash
    }, sort_keys=True).encode()
    
    return hashlib.sha256(block_string).hexdigest()
