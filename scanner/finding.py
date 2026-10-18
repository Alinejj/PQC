from dataclasses import dataclass


@dataclass
class Finding:
    file: str            
    line: int            
    matched_text: str    
    algorithm: str       
    category: str       
    status: str          
    replacement: str     