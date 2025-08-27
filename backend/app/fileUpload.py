import ipfshttpclient

def uploadImageIPFS(image):
    client = ipfshttpclient.connect()

    res = client.add(image)

    cid = res['Hash']
    return cid