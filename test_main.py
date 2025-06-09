from fastapi.testclient import TestClient
from env.main import app,Item,items

client=TestClient(app)

def test_helloworld():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() ==  "Hello world"

def test_item():
    items.clear()
    items.append({"text": "apple", "isdone": False})
    items.append({"text": "lemon", "isdone": True})
    items.append({"text": "grape", "isdone": False})
    response=client.get("/items?limit=2")
    assert response.status_code == 200
    assert response.json() ==  [{
        "text": "apple",
        "isdone": False
    },
    {
        "text": "lemon",
        "isdone": True
    }
]
    
def test_additem():
    items.clear()
    response = client.post("/items",json={"text": "apple"})
    assert response.status_code == 200
    assert response.json()["text"] == "apple"

def test_itemid():
    items.clear()
    items.append({"text": "apple", "isdone": False})
    response=client.get("items/0")
    assert response.status_code==200
    assert response.json()["text"]=="apple"

def test_update():
    items.clear()
    items.append({"text": "apple", "isdone": False})
    response=client.put("/status",json={"text": "apple", "isdone": True})
    assert response.status_code==200
    assert response.json()["isdone"]==True



    
