import os
from anthropic import Anthropic
from utils import save_LLM_output
import re
import yaml
from loguru import logger


class Claude:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    client = Anthropic(api_key=api_key)

    def get_system_block(self, system_prompt="", research_block_1="", research_block_2="", plan=""):
        """The order of the different blocks is thought to optimize token usage, using the cache strategy"""

        system_block = []

        if system_prompt:
            system_block.append({
                    "type": "text",
                    "text": system_prompt
                })

        if research_block_1:
            system_block.append({
                    "type": "text",
                    "text": research_block_1,
                    # "cache_control": {"type": "ephemeral"}
                })

        if research_block_2:
            system_block.append({
                "type": "text",
                "text": research_block_2,
                # "cache_control": {"type": "ephemeral"}
            })

        if plan:
            system_block.append({
                "type": "text",
                "text": plan,
                # "cache_control": {"type": "ephemeral"}
            })

        return system_block

    def get_yaml(self, pydantic_schema, content, system_prompt="", research_block_1="", research_block_2="", plan="", temperature=1):

        logger.debug("get_yaml")
        match = re.search(r"```(?:yaml|yml)\s*(.*?)\s*(:?```|$)", claude_response, re.DOTALL)
        yaml_str = match.group(1).strip() if match else claude_response.strip()

        try:
            raw_data = yaml.safe_load(yaml_str)
            validated_data = pydantic_schema.model_validate(raw_data)
            return validated_data

        except Exception as e:
            logger.error(f"Claude response : {claude_response}")
            save_LLM_output(claude_response, "Claude_Sonnet_4_6")
            logger.error(f"[Error]: {e}")
            return None

    def get_json(self, pydantic_schema, content, system_prompt="", research_block_1="", research_block_2="", plan="", temperature=1):
        # synchronous http call, return json matching pydantic classes
        # claude_response = self.get_text(content, system_prompt, research_block_1, research_block_2, plan, temperature)
        claude_response = """
```json
{
  "titre_audioguide": "Paris Médiéval : Enquête Forensique sur la Capitale des Capétiens",
  "strategie": "Paris sous les Capétiens et les Valois. Une enquête forensique sur les strates de pouvoir, de foi et de violence qui ont sculpté l'île de la Cité et ses faubourgs. Le fil rouge : comment une bourgade franque est devenue la capitale intellectuelle et politique de l'Occident médiéval, et à quel prix humain.",
  "parcours": [
    {
      "numero": 1,
      "type": "Respiration_Contexte",
      "titre_etape": "Le Parvis Zéro : Ce que le Sol a Avalé",
      "localisation": "Parvis Notre-Dame - Place Jean-Paul II, 75004 Paris",
      "transition_depuis_precedent": null,
      "consigne_plume": "Regardez le sol dallé du parvis et la plaque du point zéro des routes de France — puis regardez ce vide minéral, cette esplanade rasée au bulldozer par Haussmann. Ce parvis n'a rien de médiéval : c'est une amnésie urbaine délibérée. Ouvrez avec la question de ce que Paris a choisi d'effacer pour se raconter proprement, et posez le cadre de l'enquête : une île, deux mille ans de strates, un pouvoir qui réécrit le sol à chaque génération.",
      "cible_duree_audio": "2 minutes",
      "is_grand_format": false,
      "faits_retenus": [],
      "briefs_recherche_additionnelle": [
        "Mission pour l'agent chercheur : Enquêter sur la démolition haussmannienne du tissu médiéval du parvis Notre-Dame — combien de rues, d'îlots, d'édifices médiévaux ont été rasés entre 1850 et 1870 pour créer le parvis actuel ? Chercher des plans comparatifs avant/après et des sources primaires sur la résistance ou l'absence de résistance à cette destruction.",
        "Mission pour l'agent chercheur : Enquêter sur la topographie de l'île de la Cité au Xe siècle — superficie, population estimée, densité du bâti, coexistence des pouvoirs (royal, épiscopal, judiciaire) dans un espace contraint. Sources : Berty et Tisserand, Topographie historique du vieux Paris, et fouilles archéologiques INRAP île de la Cité."
      ]
    },
    {
      "numero": 2,
      "type": "Vestige_Majeur",
      "titre_etape": "La Conciergerie : Quand le Palais Devient Cage",
      "localisation": "Conciergerie, 2 Boulevard du Palais, 75001 Paris",
      "transition_depuis_precedent": "Depuis le parvis, longez le flanc nord de Notre-Dame, traversez le pont au Change et remontez le quai de l'Horloge vers l'entrée de la Conciergerie — 5 minutes à pied.",
      "consigne_plume": "Pointez la Tour Bonbec, angle Seine côté ouest — lisez le panneau moderne qui mentionne pudiquement la 'question'. Ce nom, Bonbec, 'qui parle bien', est le seul aveu que le bâtiment ait jamais fait sur lui-même. Élargissez sur la mécanique du pouvoir capétien : un palais qui torture ses ennemis dans ses propres murs, qui expulse les Juifs depuis ses archives, qui fabrique la sainteté de ses rois en sous-sol — et qui se vend aujourd'hui 13 euros l'entrée avec une boutique Marie-Antoinette.",
      "cible_duree_audio": "4 minutes",
      "is_grand_format": false,
      "faits_retenus": ["ID_41", "ID_42", "ID_44", "ID_45", "ID_46", "ID_47"],
      "briefs_recherche_additionnelle": []
    },
    {
      "numero": 3,
      "type": "Vestige_Majeur",
      "titre_etape": "La Sainte-Chapelle : Le Coffre-Fort de Dieu",
      "localisation": "Sainte-Chapelle, 8 Boulevard du Palais, 75001 Paris",
      "transition_depuis_precedent": "Sortez de la Conciergerie, revenez sur le Boulevard du Palais et entrez dans la cour du Palais de Justice — la Sainte-Chapelle est à 50 mètres, cachée dans l'enceinte judiciaire.",
      "consigne_plume": "Entrez par la chapelle basse et restez-y — ne montez pas encore. Regardez le plafond bas, les colonnes trapues, l'absence totale de lumière. C'est ici que priaient les serviteurs. La hiérarchie spatiale est gravée dans la pierre : le peuple de Paris n'a jamais mis les pieds dans la chapelle haute. Élargissez sur la machine politique que Louis IX a construite : 135 000 livres tournois pour une couronne d'épines mise en gage à Venise par un empereur en faillite — soit trois fois le coût de la chapelle elle-même — et une bulle papale pour court-circuiter l'évêque de Paris. La sainteté, ici, a un prix de revient documenté.",
      "cible_duree_audio": "8 minutes",
      "is_grand_format": true,
      "faits_retenus": ["ID_8", "ID_9", "ID_10", "ID_11", "ID_72", "ID_73", "ID_74", "ID_75", "ID_76", "ID_77", "ID_78", "ID_79"],
      "briefs_recherche_additionnelle": [
        "Mission pour l'agent chercheur : Enquêter sur le programme iconographique des vitraux de la Sainte-Chapelle comme discours politique codé — identifier les scènes où Louis IX est représenté en équivalent christique, les séquences où la légitimité capétienne est mise en parallèle avec les rois de l'Ancien Testament, et les anomalies de repose signalées par le Corpus Vitrearum après la restauration Viollet-le-Duc de 1845. Sources primaires : Corpus Vitrearum Medii Aevi, France, vol. I ; comptes royaux de la construction (1241-1248) publiés par Léon Le Grand.",
        "Mission pour l'agent chercheur : Enquêter sur la circulation diplomatique des reliques au XIIIe siècle — comment Louis IX a redistribué des fragments de la Couronne d'Épines et d'autres reliques de la Passion à des cours européennes (Castille, Norvège, Angleterre) pour structurer un réseau d'alliances. Chercher les actes de donation conservés dans les Layettes du Trésor des Chartes et les travaux de William Chester Jordan sur la politique religieuse de Louis IX."
      ]
    },
    {
      "numero": 4,
      "type": "Vestige_Majeur",
      "titre_etape": "Notre-Dame : Le Chantier comme Laboratoire Social",
      "localisation": "Cathédrale Notre-Dame de Paris, Parvis Notre-Dame, 75004 Paris",
      "transition_depuis_precedent": "Ressortez du Palais de Justice par le portail du Boulevard du Palais, retraversez vers le parvis — Notre-Dame est à 200 mètres plein est.",
      "consigne_plume": "Regardez la façade ouest et cherchez les ruptures dans l'appareillage de pierre entre les deux tours — la tour sud a été achevée une génération après la tour nord, et ça se voit dans le grain du calcaire. Élargissez sur l'économie invisible du chantier : les comptes royaux listent les livres dépensées, jamais les noms des carriers de Vaugirard ni des tailleurs de pierre morts de silicose. Et pendant ce temps, le chapitre cathédral menait une guerre juridictionnelle permanente contre le roi — un contre-pouvoir en dentelle de pierre.",
      "cible_duree_audio": "4 minutes",
      "is_grand_format": false,
      "faits_retenus": ["ID_1", "ID_2", "ID_3"],
      "briefs_recherche_additionnelle": []
    },
    {
      "numero": 5,
      "type": "Vestige_Majeur",
      "titre_etape": "La Juiverie Effacée : Rue de la Cité, Angle du Crime",
      "localisation": "Rue de la Cité (ancienne rue de la Juiverie), entre le parvis Notre-Dame et l'Hôtel-Dieu, 75004 Paris",
      "transition_depuis_precedent": "Depuis le parvis, prenez la rue de la Cité vers le nord — vous marchez littéralement sur l'ancienne Juiverie médiévale.",
      "consigne_plume": "Regardez l'absence : aucune plaque, aucune stèle, aucun marqueur mémoriel sur cette rue. Le nom lui-même — rue de la Cité — a remplacé rue de la Juiverie. Élargissez sur le cycle d'extorsion institutionnalisé : expulsion 1182, retour monnayé, expulsion 1306 avec saisie des créances, rappel payant en 1315, re-expulsion 1323, et clôture définitive en 1394 — chaque présence juive à Paris était une ressource fiscale ponctuelle pour la couronne capétienne, et chaque départ laissait le Trésor royal bénéficiaire.",
      "cible_duree_audio": "3 minutes",
      "is_grand_format": false,
      "faits_retenus": ["ID_22", "ID_23", "ID_24", "ID_25", "ID_26", "ID_44", "ID_45"],
      "briefs_recherche_additionnelle": []
    },
    {
      "numero": 6,
      "type": "Respiration_Contexte",
      "titre_etape": "Le Pont au Change : Artère Marchande, Nœud de Contrôle",
      "localisation": "Pont au Change, 75001 Paris",
      "transition_depuis_precedent": "Remontez vers le nord, traversez le Pont au Change — arrêtez-vous au milieu du pont.",
      "consigne_plume": "Regardez en aval vers la Seine et imaginez les péniches de la Hanse parisienne déchargeant leurs marchandises sur la berge de Grève — ce pont était un point de péage et de contrôle. Déroulez ici le contexte macro de l'économie fluviale médiévale : les Marchands de l'Eau tenaient le monopole du déchargement, finançaient la prévôté, et c'est depuis cette logique de contrôle portuaire qu'Étienne Marcel a construit son pouvoir.",
      "cible_duree_audio": "1 minute 30",
      "is_grand_format": false,
      "faits_retenus": [],
      "briefs_recherche_additionnelle": []
    },
    {
      "numero": 7,
      "type": "Vestige_Majeur",
      "titre_etape": "Place du Châtelet : L'Architecture de la Peur",
      "localisation": "Place du Châtelet, 75001 Paris",
      "transition_depuis_precedent": "Traversez le Pont au Change jusqu'à la rive droite — vous arrivez directement place du Châtelet.",
      "consigne_plume": "Regardez la fontaine du Palmier au centre de la place et le vide minéral qui l'entoure — aucun vestige, aucune pierre du Grand Châtelet qui se dressait ici. Élargissez sur ce que ce vide signifie : une forteresse carolingienne de 877 reconvertie en machine judiciaire, six salles de torture documentées, 127 cas criminels dans le seul registre de 1389-1392 conservé aux Archives nationales — et une démolition en 1802 qui a effacé jusqu'aux fondations.",
      "cible_duree_audio": "3 minutes",
      "is_grand_format": false,
      "faits_retenus": ["ID_12", "ID_13", "ID_14", "ID_15", "ID_16", "ID_17", "ID_18"],
      "briefs_recherche_additionnelle": []
    },
    {
      "numero": 8,
      "type": "Vestige_Majeur",
      "titre_etape": "Place de l'Hôtel de Ville : La Grève — Berge des Damnés",
      "localisation": "Place de l'Hôtel de Ville, 75004 Paris",
      "transition_depuis_precedent": "Depuis la place du Châtelet, remontez le quai de Gesvres vers l'est sur 300 mètres — vous arrivez place de l'Hôtel de Ville.",
      "consigne_plume": "Regardez la patinoire hivernale ou les gradins du concert estival — puis regardez le sol plat et comprenez que le niveau médiéval est à trois mètres sous vos pieds. Élargissez sur la triple fonction de cet espace : marché du travail non régulé où les journaliers attendaient l'embauche (trop pauvres pour figurer dans les registres fiscaux), espace d'exécution publique où les Maillotins furent décapités en 1382, et scène du meurtre politique d'Étienne Marcel — un espace que la République a transformé en esplanade festive sans une seule plaque mémorielle médiévale.",
      "cible_duree_audio": "3 minutes",
      "is_grand_format": false,
      "faits_retenus": ["ID_62", "ID_63", "ID_64", "ID_65", "ID_66", "ID_67", "ID_68", "ID_69", "ID_70", "ID_71"],
      "briefs_recherche_additionnelle": []
    },
    {
      "numero": 9,
      "type": "Vestige_Majeur",
      "titre_etape": "La Révolte d'Étienne Marcel : Le Meurtre dans la Chambre du Dauphin",
      "localisation": "Palais de la Cité (Palais de Justice), 10 Boulevard du Palais, 75001 Paris — côté entrée principale",
      "transition_depuis_precedent": "Retraversez la Seine par le Pont Notre-Dame ou le Pont d'Arcole et revenez sur l'île de la Cité par le Boulevard du Palais — 7 minutes à pied.",
      "consigne_plume": "Regardez la façade néoclassique du Palais de Justice et cherchez, derrière elle, le palais médiéval englouti. C'est dans les salles de ce palais que Marcel a fait assassiner deux maréchaux de France devant le dauphin le 22 février 1358, puis contraint ce même dauphin à porter le chaperon rouge et bleu de Paris. Élargissez sur ce que cet épisode révèle : la première tentative d'un pouvoir municipal de constitutionnaliser la monarchie française — et son échec sanglant cinq mois plus tard à la porte Saint-Antoine.",
      "cible_duree_audio": "3 minutes",
      "is_grand_format": false,
      "faits_retenus": ["ID_43", "ID_51", "ID_52", "ID_53", "ID_54", "ID_55", "ID_56", "ID_57"],
      "briefs_recherche_additionnelle": []
    },
    {
      "numero": 10,
      "type": "Vestige_Majeur",
      "titre_etape": "L'Enclos du Temple : La Zone Franche Détruite",
      "localisation": "Square du Temple, rue de Bretagne, 75003 Paris",
      "transition_depuis_precedent": "Quittez l'île de la Cité par le Pont au Change, remontez la rue de Rivoli puis la rue du Temple vers le nord jusqu'au square du Temple — 20 minutes à pied ou 2 stations de métro (ligne 11, Arts et Métiers).",
      "consigne_plume": "Regardez le square verdoyant et les enfants qui jouent — puis regardez le périmètre : rue du Temple, rue de Bretagne, rue de Picardie, rue Béranger. Ce rectangle est l'empreinte exacte de l'enclos templier, six hectares d'immunité juridique totale hors de toute juridiction royale ou épiscopale. Élargissez sur la destruction de l'Ordre en 1307 comme opération d'État : une arrestation simultanée dans tout le royaume un vendredi 13 octobre, des aveux produits sous torture dans les tours du Palais de la Cité, une bulle papale de suppression sans condamnation judiciaire — et Jacques de Molay brûlé vif en 1314 à l'île aux Juifs, à l'emplacement de l'actuel square du Vert-Galant.",
      "cible_duree_audio": "4 minutes",
      "is_grand_format": false,
      "faits_retenus": ["ID_29", "ID_30", "ID_31", "ID_32", "ID_33", "ID_34"],
      "briefs_recherche_additionnelle": []
    },
    {
      "numero": 11,
      "type": "Vestige_Majeur",
      "titre_etape": "La Tour Jean-sans-Peur : L'Architecture de la Culpabilité",
      "localisation": "Tour Jean-sans-Peur, 20 rue Étienne-Marcel, 75002 Paris",
      "transition_depuis_precedent": "Du square du Temple, descendez la rue du Temple vers le sud, puis prenez la rue Étienne-Marcel vers l'ouest sur 400 mètres.",
      "consigne_plume": "Regardez la tour et son escalier à vis visible depuis la rue — c'est le seul vestige en élévation de l'hôtel des ducs de Bourgogne. Jean sans Peur la fait construire en 1409, deux ans après avoir fait assassiner Louis d'Orléans dans une rue de Paris. Élargissez sur la guerre civile Armagnacs-Bourguignons comme contexte de la révolte cabochienne de 1413 : les bouchers de la Grande Boucherie, menés par Simon Caboche dit l'écorcheur, comme bras armé de la faction bourguignonne — la corporation la plus sanglante de Paris au sens propre comme au sens figuré.",
      "cible_duree_audio": "3 minutes",
      "is_grand_format": false,
      "faits_retenus": ["ID_51", "ID_85", "ID_86", "ID_87", "ID_88"],
      "briefs_recherche_additionnelle": []
    },
    {
      "numero": 12,
      "type": "Vestige_Majeur",
      "titre_etape": "Les Saints-Innocents : La Fosse Commune de l'Occident",
      "localisation": "Place Joachim-du-Bellay (ancienne emprise du cimetière des Saints-Innocents), 75001 Paris",
      "transition_depuis_precedent": "Depuis la tour Jean-sans-Peur, continuez rue Étienne-Marcel vers l'ouest puis descendez vers les Halles — place Joachim-du-Bellay est à 5 minutes.",
      "consigne_plume": "Regardez la fontaine des Innocents et le sol de la place — sous vos pieds et dans un rayon de 100 mètres se trouvait le cimetière le plus saturé d'Europe médiévale. En 1348, plus de 500 corps par jour y étaient portés selon Jean de Venette. Élargissez sur ce que la Peste Noire a fait à Paris : un tiers de la population morte en dix-huit mois, une vacance foncière massive, une ordonnance royale bloquant les salaires dès 1351 pour empêcher les survivants de négocier leur rareté — et une Faculté de Médecine qui expliquait l'épidémie par la conjonction de Mars, Jupiter et Saturne.",
      "cible_duree_audio": "3 minutes",
      "is_grand_format": false,
      "faits_retenus": ["ID_89", "ID_90", "ID_91", "ID_92", "ID_93", "ID_94", "ID_95"],
      "briefs_recherche_additionnelle": []
    },
    {
      "numero": 13,
      "type": "Respiration_Contexte",
      "titre_etape": "Le Tracé Fantôme de Philippe Auguste : Marcher sur les Remparts",
      "localisation": "Rue Saint-Jacques / Rue des Fossés-Saint-Bernard, 75005 Paris (tracé enceinte Philippe Auguste, rive gauche)",
      "transition_depuis_precedent": "Traversez la Seine par le Pont au Change ou le Pont Saint-Michel, remontez vers la rive gauche et engagez-vous rue Saint-Jacques vers le sud — vous marchez sur l'axe du cardo romain et dans l'enceinte de Philippe Auguste.",
      "consigne_plume": "Regardez le sol de la rue Saint-Jacques et imaginez le cardo romain en dessous — les fouilles INRAP ont révélé plusieurs couches de pavage superposées. Déroulez ici la logique des deux enceintes successives : Philippe Auguste (1190-1215) qui enferme la rive gauche, Charles V (1356-1383) qui étend la rive droite seulement — une asymétrie révélatrice de où se trouvait la richesse fiscale de Paris.",
      "cible_duree_audio": "2 minutes",
      "is_grand_format": false,
      "faits_retenus": ["ID_4", "ID_28"],
      "briefs_recherche_additionnelle": []
    },
    {
      "numero": 14,
      "type": "Vestige_Majeur",
      "titre_etape": "Le Quartier des Écoles : La Rue du Fouarre et l'Hérésie Organisée",
      "localisation": "Rue du Fouarre, 75005 Paris",
      "transition_depuis_precedent": "Depuis la rue Saint-Jacques, descendez vers la Seine et prenez la rue du Fouarre — petite rue à gauche avant le quai.",
      "consigne_plume": "Regardez le nom de la rue gravé sur la plaque — 'Fouarre' signifie 'paille' : les étudiants s'asseyaient sur de la paille pour écouter les maîtres. C'est ici que Siger de Brabant enseignait l'aristotélisme radical avant d'être condamné par 219 thèses en 1277 et de finir assassiné à Orvieto. Élargissez sur la bulle Parens Scientiarum de 1231 qui a soustrait l'Université à la juridiction de l'évêque de Paris — une indépendance intellectuelle arrachée par la grève et consacrée par Rome, qui a fait de Paris la capitale intellectuelle de l'Occident médiéval au prix d'une guerre permanente contre le chapitre Notre-Dame.",
      "cible_duree_audio": "3 minutes",
      "is_grand_format": false,
      "faits_retenus": ["ID_5", "ID_7"],
      "briefs_recherche_additionnelle": []
    },
    {
      "numero": 15,
      "type": "Vestige_Majeur",
      "titre_etape": "La Tour Clovis : Ce qui Reste de Sainte-Geneviève",
      "localisation": "Tour Clovis, Lycée Henri-IV, 23 rue Clovis, 75005 Paris (visible depuis la rue)",
      "transition_depuis_precedent": "Remontez la rue Saint-Jacques vers le sud, prenez la rue Clovis sur la gauche — la tour est visible depuis la rue en longeant le lycée Henri-IV.",
      "consigne_plume": "Regardez la base de la tour Clovis qui dépasse au-dessus du mur du lycée — c'est le seul vestige en élévation de l'abbaye Sainte-Geneviève, fondée selon la chronologie officielle par Clovis en 502, reconstruite après les Vikings. Élargissez sur la concurrence de pouvoirs sacrés dans Paris médiéval : une abbaye exemptée de l'autorité épiscopale par Honorius III en 1222, qui gérait ses propres serfs, levait ses propres taxes, et constituait un pôle scolaire rival de Notre-Dame — deux institutions ecclésiastiques se disputant le monopole de la légitimité intellectuelle sur la même colline.",
      "cible_duree_audio": "2 minutes 30",
      "is_grand_format": false,
      "faits_retenus": ["ID_48", "ID_49", "ID_50"],
      "briefs_recherche_additionnelle": []
    },
    {
      "numero": 16,
      "type": "Vestige_Majeur",
      "titre_etape": "Saint-Germain-des-Prés : La Seigneurie dans la Ville",
      "localisation": "Abbaye Saint-Germain-des-Prés, Place Saint-Germain-des-Prés, 75006 Paris",
      "transition_depuis_precedent": "Depuis la rue Clovis, descendez vers la Seine, traversez par le Pont de la Tournelle ou le Pont au Double, remontez vers Saint-Germain-des-Prés — 15 minutes à pied.",
      "consigne_plume": "Regardez les colonnes de marbre et les chapiteaux mérovingiens réemployés dans la nef — ces fûts ont été arrachés à un temple antique ou à une basilique antérieure et recyclés au VIe siècle. Élargissez sur ce que cette abbaye était réellement au Moyen Âge : une seigneurie indépendante avec ses propres serfs (documentés dans le polyptyque d'Irminon), sa propre foire annuelle attestée dès 1176, sa propre justice, et un conflit avec l'évêque de Paris si aigu qu'Alexandre III a exclu Maurice de Sully de la consécration du chœur en 1163.",
      "cible_duree_audio": "3 minutes",
      "is_grand_format": false,
      "faits_retenus": ["ID_58", "ID_59", "ID_60", "ID_82"],
      "briefs_recherche_additionnelle": []
    },
    {
      "numero": 17,
      "type": "Vestige_Majeur",
      "titre_etape": "Les Arènes de Lutèce : Le Monument que Paris a Choisi d'Oublier",
      "localisation": "Arènes de Lutèce, 49 rue Monge / entrée rue de Navarre, 75005 Paris",
      "transition_depuis_precedent": "Depuis Saint-Germain-des-Prés, traversez la Seine et remontez vers la rue Monge — les arènes sont à 15 minutes à pied ou 2 stations de métro (ligne 7, Place Monge).",
      "consigne_plume": "Regardez les gradins de calcaire et cherchez les lacunes, les blocs manquants, les rangées incomplètes — ce que vous voyez est ce que le Moyen Âge n'a pas eu le temps de voler. Dès la fin du IIIe siècle, les blocs ont été arrachés pour construire l'enceinte gallo-romaine de l'île de la Cité. Élargissez sur la mémoire sélective de Paris : ce monument était enfoui sous un terrain appartenant à l'abbaye Saint-Victor depuis 1108, traversé par un canal de la Bièvre, utilisé comme cimetière médiéval — et c'est Victor Hugo qui a écrit la lettre qui a sauvé ce qui restait en 1883, quand la Compagnie des omnibus voulait y construire un dépôt de bus.",
      "cible_duree_audio": "3 minutes",
      "is_grand_format": false,
      "faits_retenus": ["ID_35", "ID_36", "ID_37", "ID_38", "ID_39", "ID_40"],
      "briefs_recherche_additionnelle": []
    },
    {
      "numero": 18,
      "type": "Vestige_Majeur",
      "titre_etape": "Vincennes : Le Bunker des Valois",
      "localisation": "Château de Vincennes, Avenue de Paris, 94300 Vincennes",
      "transition_depuis_precedent": "Depuis les arènes, rejoignez la station Nation (métro ligne 1) et prenez la ligne 1 jusqu'au terminus Château de Vincennes — 20 minutes.",
      "consigne_plume": "Regardez les murs du donjon et posez votre main dessus si vous pouvez — 3,20 mètres d'épaisseur. Ce n'est pas de l'architecture, c'est de la paranoïa dynastique coulée dans la pierre. Élargissez sur la fonction réelle de Vincennes : construit à partir de 1337 au début de la Guerre de Cent Ans comme résidence sécurisée quand Paris devient dangereuse, utilisé par Charles V comme coffre-fort du trésor royal au deuxième étage, et refuge systématique de la royauté lors des soulèvements parisiens — dont la révolte cabochienne de 1413. Un château à 8 kilomètres de Paris, c'est exactement la distance qu'il faut pour régner sans être lynché.",
      "cible_duree_audio": "3 minutes",
      "is_grand_format": false,
      "faits_retenus": ["ID_19", "ID_20", "ID_21"],
      "briefs_recherche_additionnelle": []
    }
  ]
}
```
       """
       
        logger.debug("get_json")
        
        # Delete markdown json claude often sends at the beginning of its response...
        match = re.search(r"```json\s*(.*?)\s*```", claude_response, re.DOTALL)
        # First group is the json markdown, so we select the second
        json_str = match.group(1).strip() if match else claude_response.strip()

        try:
            validated_data = pydantic_schema.parse_raw(json_str)
            return validated_data

        except Exception as e:
            logger.error(f"Claude response : {claude_response}")
            save_LLM_output(claude_response, "Claude_Sonnet_4_6")
            logger.error(f"[Error]: {e}")
            return None

    def get_text(self, content, system_prompt="", research_block_1="", research_block_2="", plan="", temperature=1):
        # synchronous http call, wait for the full text to be generated
        try:
            logger.info("Avant appel claude")

            system_block = self.get_system_block(system_prompt, research_block_1, research_block_2, plan)
            # save_LLM_output(system_block, "System_block")

            # logger.debug(f"content : {content}")
            logger.debug(f"Claude system_block : {system_block}")
            response = self.client.messages.create(
                max_tokens=16384,
                system=system_block,
                temperature=temperature,
                messages=[
                    {
                        "role": "user",
                        "content": content
                    }
                ],
                model="claude-sonnet-4-6",
            )
            logger.info("Après appel claude")
            logger.debug(response)

            return response.content[0].text
        except Exception as e:
            logger.error(f"Claude [Error]: {e}")
            save_LLM_output(response, "Claude_Sonnet_4_6")