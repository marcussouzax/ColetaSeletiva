import os

print("Pasta atual:")
print(os.getcwd())

print("\nArquivos .db encontrados:")

for raiz, dirs, arquivos in os.walk("."):
    for arquivo in arquivos:
        if arquivo.endswith(".db"):
            print(os.path.join(raiz, arquivo))