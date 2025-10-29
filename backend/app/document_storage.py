from typing import Dict, List
import json
import os

class DocumentStorage:
    def __init__(self, storage_file: str = "documents_db.json"):
        self.storage_file = storage_file
        self.documents: Dict[str, List[dict]] = {}
        self.load()
    
    def load(self):
        """Load documents from file."""
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r') as f:
                    self.documents = json.load(f)
            except Exception as e:
                print(f"Error loading documents: {e}")
                self.documents = {}
    
    def save(self):
        """Save documents to file."""
        try:
            with open(self.storage_file, 'w') as f:
                json.dump(self.documents, f, indent=2)
        except Exception as e:
            print(f"Error saving documents: {e}")
    
    def add_document(self, wallet: str, doc_data: dict):
        """Add a document for a wallet."""
        wallet = wallet.lower()
        if wallet not in self.documents:
            self.documents[wallet] = []
        
        self.documents[wallet].append(doc_data)
        self.save()
    
    def get_documents(self, wallet: str) -> List[dict]:
        """Get all documents for a wallet."""
        wallet = wallet.lower()
        return self.documents.get(wallet, [])
    
    def remove_document(self, wallet: str, ipfs_cid: str) -> bool:
        """Remove a specific document by CID."""
        wallet = wallet.lower()
        if wallet not in self.documents:
            return False
        
        initial_len = len(self.documents[wallet])
        self.documents[wallet] = [
            doc for doc in self.documents[wallet] 
            if doc.get('ipfs_cid') != ipfs_cid
        ]
        
        if len(self.documents[wallet]) < initial_len:
            self.save()
            return True
        return False

# Global instance
doc_store = DocumentStorage()
