def test_create_and_get_car(client,allowed):
    payload = {"name": "Tesla", "hp": 500, "model": "Model S","owner_id":1}
    response = client.post("/add", json=payload)
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Tesla"
    car_id = data["id"]


    response = client.get("/")
    assert response.status_code == 200
    assert len(response.json()["data"]) == 1
    assert response.json()["data"][0]["name"] == "Tesla"  

def test_UpdateCar(client,allowed):
    payload={"name":"tesla","hp":600,"model":"model s"}    
    response=client.post("/add",json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "tesla"
    car_id = data["id"]

    payload={"name":"tesla","hp":600,"model":"model y"}  
    response=client.put(F"/update/{car_id}",json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["model"] == "model y"
    assert data["id"] == car_id

def test_Deletecar(client,allowed):
    payload={"name":"tesla","hp":500,"model":"model xy"}
    response=client.post("/add",json=payload)
    assert response.status_code==201
    data=response.json()
    assert data["name"]=="tesla"
    car_id=data["id"]  

    response=client.delete(f"/delete/{car_id}")
    assert response.status_code==204


