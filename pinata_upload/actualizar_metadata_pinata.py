import os
import json

# 1. CID de las imágenes subidas a Pinata (el que me diste)
IMAGES_CID = "bafybeidoj4dc4w3yvngqsufvcmpuhcszsqnxmzx6wqsbikseekqqnpy6l4"

# 2. Carpeta donde están TODOS tus JSON de metadata (copiados o preparados)
METADATA_FOLDER = r"C:\EmberholmServer\metadata_final"

# 3. Recorremos cada archivo .json y lo actualizamos
updated = 0
for filename in sorted(os.listdir(METADATA_FOLDER)):
    if not filename.lower().endswith(".json"):
        continue

    token_id = filename.replace(".json", "")  # ejemplo: "00001"
    json_path = os.path.join(METADATA_FOLDER, filename)

    # Abrimos la metadata existente
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Aseguramos que tenga 'name' y 'description' (por si alguno está incompleto)
    if "name" not in data:
        data["name"] = f"Emissary {token_id}"
    if "description" not in data:
        data["description"] = "Emissary of Emberholm."

    # 💥 Punto clave:
    # Seteamos la URL pública IPFS de la imagen correcta de ese token
    data["image"] = f"ipfs://{IMAGES_CID}/{token_id}.png"

    # (Opcional futuro) podríamos agregar un external_url que apunte al Portal oficial
    # data["external_url"] = f"https://emberholm-portal.example/emissary/{token_id}"

    # Guardamos de vuelta el JSON con pretty-print
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    updated += 1

print(f"✅ Listo. Metadatas actualizadas: {updated}")
print("Ahora podés subir la carpeta 'metadata_final' entera a Pinata.")
