import sys
import os

sys.path.append(os.path.join(os.getcwd(), "scripts"))
from nb_client import NbClient

client = NbClient(notebook="jbot")
notes = client.ls()
for n in notes:
    print(f"ID: {n.id}, Title: {n.title}")
    if "ADR-210" in n.title:
        content = client.show(n.id)
        print(f"Content for {n.id} found: {content is not None}")
