import os
import sys

def fusionner(dossier_source):
    # On normalise le chemin pour éviter les emmerdes de slashs
    dossier = os.path.abspath(dossier_source)
    fichier_final = os.path.join(dossier, "ALERTE_FUSION.txt")
    separateur = "-" * 15

    if not os.path.isdir(dossier):
        print(f"Erreur : '{dossier}' n'est pas un dossier valide, gros malin.")
        return

    with open(fichier_final, "w", encoding="utf-8") as outfile:
        # On trie pour pas que ce soit le bordel
        fichiers = sorted([f for f in os.listdir(dossier) if f.endswith(".txt") and f != "ALERTE_FUSION.txt"])
        
        for nom in fichiers:
            chemin_complet = os.path.join(dossier, nom)
            # Construction de l'en-tête
            outfile.write(f"\n{separateur}\n{nom.upper()}\n{separateur}\n\n")
            
            with open(chemin_complet, "r", encoding="utf-8", errors="ignore") as infile:
                outfile.write(infile.read())
            outfile.write("\n")

    print(f"C'est fini. Ton pavé est là : {fichier_final}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        fusionner(sys.argv[1])
    else:
        path = input("File-moi le chemin du dossier : ").strip('"')
        fusionner(path)