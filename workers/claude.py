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
{
  "titre_audioguide": "Paris Médiéval : Autopsie d'une Capitale",
  "strategie": "Paris sous les Capétiens et les Valois. Une enquête forensique sur les strates de pouvoir, de foi et de violence qui ont sculpté l'île de la Cité et ses faubourgs. Le fil rouge : comment une bourgade franque est devenue la capitale intellectuelle et politique de l'Occident médiéval, et à quel prix humain.",
  "parcours": [
    {
      "numero": 1,
      "type": "Vestige_Majeur",
      "titre_etape": "La Conciergerie : Quand le Palais Devient Geôle",
      "localisation": "2 Boulevard du Palais, 75001 Paris. Entrée principale côté Seine, angle de la Tour Bonbec.",
      "transition_vers_suivant": "Remontez le long de la façade vers l'est, jusqu'à l'entrée de la Sainte-Chapelle dans la cour du Palais de Justice — le portail gothique est visible depuis le trottoir.",
      "consigne_plume": "Pointez la Tour Bonbec, à l'angle ouest de la façade sur Seine : son nom médiéval signifie littéralement 'qui parle bien', euphémisme pour la tour de torture où l'on faisait avouer les suspects. Élargissez sur la mécanique du Palais de la Cité comme machine à produire du pouvoir capétien : ici, en une seule semaine d'octobre 1307, Philippe IV a fait torturer les Templiers dans les salles basses de ce même bâtiment, après avoir fait expulser les Juifs de France un an plus tôt depuis ce même palais — le lieu est un condensé de la violence d'État médiévale, aujourd'hui vendu 13 euros avec boutique souvenir.",
      "cible_duree_audio": "3 minutes",
      "is_grand_format": false,
      "faits_retenus": ["ID_46", "ID_47", "ID_41", "ID_45"],
      "briefs_recherche_additionnelle": []
    },
    {
      "numero": 2,
      "type": "Vestige_Majeur",
      "titre_etape": "La Sainte-Chapelle : Le Coffre-Fort de Dieu",
      "localisation": "8 Boulevard du Palais, 75001 Paris. Entrée par la cour intérieure du Palais de Justice, après le portique de sécurité.",
      "transition_vers_suivant": "Ressortez dans la cour, traversez le boulevard du Palais et prenez la rue de la Cité vers le nord — vous marchez sur l'axe exact de l'ancienne rue de la Juiverie médiévale.",
      "consigne_plume": "Dis à l'auditeur de trouver un endroit pour s'asseoir et écouter. Depuis votre siège, levez les yeux sur la rose occidentale — cette verrière entière est un faux du XVe siècle, commandé par Charles VIII, et les deux tiers des autres panneaux ont été remontés à l'envers ou intervertis par Viollet-le-Duc en 1845 : vous regardez un récit iconographique partiellement incohérent sans le savoir. Élargissez sur la Sainte-Chapelle comme opération de communication politique totale : Louis IX a payé 135 000 livres tournois pour racheter la Couronne d'Épines — trois fois le coût de construction de la chapelle elle-même — à une dette vénitienne de l'empereur fantoche de Constantinople, puis a bâti ce reliquaire géant à l'intérieur de son palais privé, inaccessible au peuple, pour se positionner comme roi-prêtre au-dessus de l'évêque de Paris et de la papauté ; et quand son petit-fils Philippe IV l'a fait canoniser en 1297, la chapelle est devenue rétroactivement un lieu de pèlerinage dynastique — la sainteté comme outil de gouvernement.",
      "cible_duree_audio": "8 minutes",
      "is_grand_format": true,
      "faits_retenus": ["ID_8", "ID_10", "ID_11", "ID_72", "ID_73", "ID_74", "ID_75", "ID_77", "ID_78", "ID_79", "ID_9"],
      "briefs_recherche_additionnelle": [
        {
          "name": "Programme iconographique Sainte-Chapelle : encodage du pouvoir royal",
          "angle": "Identifier précisément quelles scènes des vitraux représentent Louis IX en figure christique ou impériale, et dans quelle mesure le programme iconographique de 1241-1248 a été modifié après la canonisation de 1297 pour intégrer le culte dynastique — chercher les ajouts post-1297 détectables par analyse stylistique ou chimique."
        },
        {
          "name": "Bulle Parens in Excelsis 1244 : anatomie d'une enclave canonique",
          "angle": "Analyser les conséquences concrètes de l'exemption épiscopale accordée à la Sainte-Chapelle par Innocent IV en 1244 : quels conflits de juridiction cela a-t-il générés avec le chapitre de Notre-Dame, et comment Louis IX a-t-il utilisé cette exemption pour court-circuiter l'évêque de Paris dans la hiérarchie symbolique de la ville ?"
        }
      ]
    },
    {
      "numero": 3,
      "type": "Respiration_Contexte",
      "titre_etape": "Rue de la Cité : Marcher sur la Juiverie Effacée",
      "localisation": "Rue de la Cité, 75004 Paris. Tronçon entre le parvis Notre-Dame et le pont d'Arcole — ancienne rue de la Juiverie médiévale.",
      "transition_vers_suivant": "Continuez jusqu'au parvis de Notre-Dame — la façade ouest est devant vous.",
      "consigne_plume": "Regardez le sol sous vos pieds et l'absence totale de plaque, de stèle, de marqueur quelconque sur cette rue : vous marchez sur l'emplacement exact du quartier juif le plus dense de l'île de la Cité, effacé en 1182 par Philippe Auguste qui a converti la synagogue principale en église et confisqué tous les biens. Élargissez sur le cycle d'extorsion institutionnalisé que représente la présence juive médiévale à Paris : expulsion en 1182, rappel contre paiement, expulsion en 1306 avec saisie massive des créances, rappel monnayé en 1315, re-expulsion en 1323, expulsion définitive en 1394 — la communauté juive n'est pas persécutée malgré son utilité fiscale, elle est persécutée à cause d'elle.",
      "cible_duree_audio": "2 minutes",
      "faits_retenus": [],
      "briefs_recherche_additionnelle": []
    },
    {
      "numero": 4,
      "type": "Vestige_Majeur",
      "titre_etape": "Notre-Dame : Le Chantier Comme Violence Sociale",
      "localisation": "Parvis Notre-Dame — Place Jean-Paul II, 75004 Paris. Positionnez-vous face à la façade ouest, à mi-parvis.",
      "transition_vers_suivant": "Traversez le pont Notre-Dame vers la rive droite, puis longez la rue de Rivoli vers l'ouest jusqu'à la Place du Châtelet — comptez environ 8 minutes à pied.",
      "consigne_plume": "Regardez la façade : aucune épitaphe, aucune inscription ne mentionne un seul ouvrier parmi les milliers qui ont taillé ce calcaire entre 1163 et 1250. Élargissez sur le chantier cathédral comme laboratoire de l'invisibilité sociale médiévale : les comptes royaux détaillent au centime près le coût des reliques et des vitraux, mais les 'operarii' n'ont ni nom, ni salaire documenté, ni sépulture identifiée — ils inhalaient la poussière de calcaire lutétien et mouraient de pathologies pulmonaires dans l'anonymat total, pendant que Maurice de Sully réorganisait le tissu urbain de l'île entière pour dégager l'espace du chantier, et que Philippe IV, un siècle plus tard, instrumentalisait le chapitre cathédral pour financer ses guerres en ignorant la bulle Clericis laicos.",
      "cible_duree_audio": "3 minutes",
      "is_grand_format": false,
      "faits_retenus": ["ID_2", "ID_1", "ID_3"],
      "briefs_recherche_additionnelle": []
    },
    {
      "numero": 5,
      "type": "Vestige_Majeur",
      "titre_etape": "Place du Châtelet : L'Usine à Condamnés",
      "localisation": "Place du Châtelet, 75001 Paris. Positionnez-vous au centre de la place, face à la fontaine du Palmier — l'emplacement exact du Grand Châtelet disparu.",
      "transition_vers_suivant": "Remontez la rue de Rivoli vers l'est jusqu'à la Place de l'Hôtel de Ville — cinq minutes de marche, la façade néo-Renaissance de l'Hôtel de Ville sera visible au bout de la rue.",
      "consigne_plume": "Regardez la fontaine du Palmier au centre de la place : elle est posée exactement sur les fondations du Grand Châtelet, forteresse carolingienne de 877 reconvertie en prison et tribunal royal, démolie en 1802. Élargissez sur la géographie de la terreur légale médiévale : le Prévôt de Paris instruisait ici 127 affaires criminelles documentées en trois ans (1389-1392), les suspects passaient par la 'question ordinaire' (eau) ou 'extraordinaire' (brodequins) dans les six salles de torture, et les condamnés finissaient exposés pendant des mois au gibet de Montfaucon — pendant ce temps, le Parlement de Paris contestait systématiquement la juridiction du Prévôt, non par humanisme, mais par rivalité institutionnelle.",
      "cible_duree_audio": "3 minutes",
      "is_grand_format": false,
      "faits_retenus": ["ID_12", "ID_13", "ID_15", "ID_16", "ID_17", "ID_18"],
      "briefs_recherche_additionnelle": []
    },
    {
      "numero": 6,
      "type": "Vestige_Majeur",
      "titre_etape": "Place de l'Hôtel de Ville : La Grève, Scène d'Exécutions Devenue Patinoire",
      "localisation": "Place de l'Hôtel de Ville, 75004 Paris. Positionnez-vous au centre de la place, dos à la façade de l'Hôtel de Ville.",
      "transition_vers_suivant": "Prenez la rue du Temple vers le nord, traversez la rue de Rivoli, continuez jusqu'au square du Temple dans le Marais — comptez 15 minutes à pied en traversant le cœur de l'ancien enclos templier.",
      "consigne_plume": "Regardez le sol plat et dégagé sous vos pieds : il n'y a pas une seule plaque, pas un seul marqueur rappelant que cet espace était le principal lieu d'exécution publique de Paris médiéval — roue, gibet provisoire, écartèlement. Élargissez sur la Grève comme révélateur des contradictions du pouvoir urbain médiéval : ce n'était pas une place pavée mais une berge sablonneuse où les journaliers attendaient l'embauche dans une misère structurelle que l'ordonnance de 1351 post-Peste a aggravée en plafonnant les salaires sans les plancher ; Étienne Marcel en a fait sa base de pouvoir entre 1356 et 1358, y a acheté la 'Maison aux Piliers' comme premier hôtel de ville, et la révolte des Maillotins de 1382 s'est terminée ici par des décapitations collectives ordonnées par Charles VI — aujourd'hui on y installe une patinoire en hiver.",
      "cible_duree_audio": "3 minutes",
      "is_grand_format": false,
      "faits_retenus": ["ID_62", "ID_63", "ID_64", "ID_65", "ID_66", "ID_68", "ID_69"],
      "briefs_recherche_additionnelle": []
    },
    {
      "numero": 7,
      "type": "Vestige_Majeur",
      "titre_etape": "Square du Temple : Le Trou Noir de l'Enclos Templier",
      "localisation": "Square du Temple, 75003 Paris. Entrée principale rue de Bretagne. Positionnez-vous à l'intérieur du square, face au bassin central.",
      "transition_vers_suivant": "Sortez du square par la rue de Bretagne, tournez à gauche rue du Temple, puis à droite rue Étienne-Marcel — la Tour Jean-sans-Peur est au numéro 20, reconnaissable à sa tourelle gothique dépassant des immeubles haussmanniens.",
      "consigne_plume": "Regardez ce jardin municipal ordinaire avec ses bancs et son bassin : vous êtes au centre de ce qui était l'une des zones franches les plus puissantes d'Europe médiévale, six hectares totalement hors juridiction royale et épiscopale, dont Napoléon a ordonné l'effacement total en 1808 précisément pour supprimer un lieu de pèlerinage. Élargissez sur la destruction de l'Ordre du Temple en 1307 comme modèle parfait de la prédation d'État : Philippe IV a planifié en secret l'arrestation simultanée de tous les Templiers du royaume, les a fait torturer dans les tours du Palais de la Cité pour obtenir des aveux de sodomie et d'hérésie, et quand certains ont rétracté leurs aveux, il les a brûlés vifs — Clément V a soldé l'affaire non par condamnation judiciaire mais par dissolution administrative en 1312, un compromis qui laissait les Templiers coupables sans procès équitable et Philippe IV propriétaire de leurs dettes.",
      "cible_duree_audio": "4 minutes",
      "is_grand_format": false,
      "faits_retenus": ["ID_29", "ID_30", "ID_31", "ID_32", "ID_33"],
      "briefs_recherche_additionnelle": []
    },
    {
      "numero": 8,
      "type": "Vestige_Majeur",
      "titre_etape": "Tour Jean-sans-Peur : Le Refuge du Meurtrier",
      "localisation": "20 Rue Étienne-Marcel, 75002 Paris. La tour gothique est visible en façade, intégrée dans l'immeuble.",
      "transition_vers_suivant": "Revenez sur vos pas rue Étienne-Marcel vers l'est, prenez la rue Saint-Denis vers le nord jusqu'au boulevard Saint-Denis — vous apercevrez la Porte Saint-Denis, vestige de l'enceinte de Charles V.",
      "consigne_plume": "Regardez la tourelle gothique enclavée dans l'immeuble haussmannien : c'est le seul vestige en élévation de l'hôtel des ducs de Bourgogne, construite entre 1409 et 1411 par Jean sans Peur après qu'il eut fait assassiner Louis d'Orléans dans une rue du Marais en 1407. Élargissez sur la guerre civile Armagnacs-Bourguignons comme moment où Paris cesse d'être une capitale royale pour devenir un champ de bataille factieux : les bouchers de la Grande Boucherie, menés par Simon Caboche — un écorcheur — ont fourni les muscles de la révolte cabochienne de 1413 au service des Bourguignons, et Jean sans Peur avait besoin d'une tour défensive à l'intérieur de la ville parce que la ville elle-même était en guerre.",
      "cible_duree_audio": "2 minutes",
      "is_grand_format": false,
      "faits_retenus": ["ID_51", "ID_85"],
      "briefs_recherche_additionnelle": []
    },
    {
      "numero": 9,
      "type": "Respiration_Contexte",
      "titre_etape": "Boulevard Saint-Denis : Marcher sur l'Enceinte de Charles V",
      "localisation": "Porte Saint-Denis, 98 Boulevard Saint-Denis, 75010 Paris. Positionnez-vous sous l'arc de triomphe de Louis XIV.",
      "transition_vers_suivant": "Revenez vers le centre en prenant la rue Saint-Martin vers le sud, puis traversez vers la rive gauche par le Pont au Change ou le Pont Neuf, et remontez la rue Saint-Jacques vers le sud.",
      "consigne_plume": "Regardez l'arc de triomphe de Louis XIV planté exactement à l'emplacement de la porte médiévale de l'enceinte de Charles V : le roi-soleil a remplacé une fortification par un monument à sa propre gloire, geste de réécriture urbaine caractéristique. Élargissez sur l'asymétrie révélatrice de l'enceinte de Charles V : construite entre 1356 et 1383, elle n'entoure que la rive droite — la rive gauche reste protégée par la vieille enceinte de Philippe Auguste, un siècle plus ancienne — parce que la croissance urbaine et économique de Paris médiéval s'est faite exclusivement au nord de la Seine, là où se trouvaient les Halles, les corporations, la Hanse parisienne et le port de Grève.",
      "cible_duree_audio": "2 minutes",
      "faits_retenus": [],
      "briefs_recherche_additionnelle": []
    },
    {
      "numero": 10,
      "type": "Vestige_Majeur",
      "titre_etape": "Rue du Fouarre : Là Où l'Europe Pensait",
      "localisation": "Rue du Fouarre, 75005 Paris. Courte rue entre le quai de Montebello et la rue Galande — entrez par le quai.",
      "transition_vers_suivant": "Remontez la rue Saint-Jacques vers le sud, jusqu'au lycée Henri-IV — la Tour Clovis dépasse au-dessus du mur d'enceinte, visible depuis la rue.",
      "consigne_plume": "Regardez le nom de la rue gravé sur la plaque : 'Fouarre' signifie 'paille' — les étudiants s'asseyaient sur de la paille pour écouter les cours en plein air, et ce toponyme de misère étudiante a survécu huit siècles. Élargissez sur l'Université de Paris comme puissance autonome construite contre l'évêque : la bulle Parens Scientiarum de 1231 a soustrait l'Université à la juridiction épiscopale, créant une enclave intellectuelle qui pouvait condamner ses propres maîtres — comme Siger de Brabant, dont l'évêque Tempier a fait condamner 219 thèses en 1277, forçant Siger à fuir jusqu'à Orvieto où il fut assassiné, probablement sur commande.",
      "cible_duree_audio": "3 minutes",
      "is_grand_format": false,
      "faits_retenus": ["ID_4", "ID_5", "ID_7"],
      "briefs_recherche_additionnelle": []
    },
    {
      "numero": 11,
      "type": "Vestige_Majeur",
      "titre_etape": "Tour Clovis : Ce Qui Reste de Sainte-Geneviève",
      "localisation": "Lycée Henri-IV, 23 Rue Clovis, 75005 Paris. La Tour Clovis est visible depuis la rue, dépassant du mur d'enceinte du lycée.",
      "transition_vers_suivant": "Continuez rue Clovis vers le sud — vous verrez dans quelques mètres un fragment du mur de Philippe Auguste intégré dans les façades, côté pair de la rue.",
      "consigne_plume": "Regardez la base de la Tour Clovis, seul vestige du clocher roman de l'abbaye Sainte-Geneviève : sous cette rue, des fouilles ont dégagé 32 sarcophages mérovingiens en 1807, confirmant que la colline était un pôle sacré plusieurs siècles avant les Capétiens. Élargissez sur la concurrence des pouvoirs religieux médiévaux : l'abbaye de Sainte-Geneviève était exemptée de la juridiction épiscopale — en 1163, le pape Alexandre III a explicitement exclu l'évêque Maurice de Sully de la consécration du chœur, humiliation publique documentée — créant sur la Montagne Sainte-Geneviève un pôle scolaire et spirituel concurrent à Notre-Dame, à deux cents mètres de distance.",
      "cible_duree_audio": "2 minutes",
      "is_grand_format": false,
      "faits_retenus": ["ID_48", "ID_49", "ID_50", "ID_60"],
      "briefs_recherche_additionnelle": []
    },
    {
      "numero": 12,
      "type": "Vestige_Majeur",
      "titre_etape": "Cimetière des Innocents Disparu : Place Joachim-du-Bellay",
      "localisation": "Place Joachim-du-Bellay (ancienne emprise du cimetière des Saints-Innocents), 75001 Paris. Fontaine des Innocents au centre.",
      "transition_vers_suivant": "Prenez la rue Berger vers l'est puis la rue du Renard vers le nord jusqu'à la rue de Bretagne, ou remontez directement vers la Seine par le boulevard de Sébastopol pour rejoindre l'île de la Cité — retour au point de départ pour clore la boucle.",
      "consigne_plume": "Regardez la Fontaine des Innocents au centre de cette place commerçante : elle est posée sur l'emplacement du plus grand cimetière intra-muros de Paris médiéval, saturé à l'extrême dès 1348 quand plus de 500 corps par jour y étaient portés selon Jean de Venette. Élargissez sur la Peste Noire comme révélateur brutal des limites de l'État capétien : Philippe VI a consulté la Faculté de Médecine en octobre 1348 qui a produit un *Compendium de epidemia* attribuant la contagion à une conjonction planétaire ; pendant ce temps Paris perdait un tiers de sa population, l'Hôtel-Dieu contaminait ses propres sœurs hospitalières, et la vacance foncière massive qui a suivi a restructuré toute la géographie de la propriété parisienne — et la seule réponse politique concrète de Jean II en 1351 a été de plafonner les salaires des survivants pour empêcher les journaliers de profiter de la pénurie de main-d'œuvre.",
      "cible_duree_audio": "4 minutes",
      "is_grand_format": false,
      "faits_retenus": ["ID_89", "ID_90", "ID_91", "ID_95"],
      "briefs_recherche_additionnelle": []
    },
    {
      "numero": 13,
      "type": "Vestige_Majeur",
      "titre_etape": "Île aux Juifs — Square du Vert-Galant : Le Bûcher de Molay",
      "localisation": "Square du Vert-Galant, Pointe ouest de l'île de la Cité, 75001 Paris. Descendez l'escalier depuis le Pont-Neuf jusqu'à la pointe basse.",
      "transition_vers_suivant": "Remontez vers le Pont-Neuf et traversez vers la rive gauche — Saint-Germain-des-Prés est à 15 minutes à pied vers l'ouest par les quais.",
      "consigne_plume": "Cherchez la plaque commémorative discrète à la pointe de l'île : c'est ici, sur ce qui s'appelait l'île aux Juifs, que Jacques de Molay et Geoffroy de Charnay ont été brûlés vifs le 18 mars 1314, après sept ans d'incarcération dans la Tour du Temple. Élargissez sur la malédiction de Molay comme symptôme d'une crise dynastique réelle : selon les chroniqueurs, Molay aurait depuis le bûcher cité Philippe IV et Clément V à comparaître devant Dieu dans l'année — les deux sont morts dans les mois suivants, et les quatre fils de Philippe IV sont morts sans héritier mâle entre 1314 et 1328, éteignant la lignée capétienne directe et ouvrant la Guerre de Cent Ans ; la légende de la malédiction n'est pas une superstition populaire, c'est la mise en récit d'une catastrophe dynastique réelle que personne ne savait expliquer autrement.",
      "cible_duree_audio": "3 minutes",
      "is_grand_format": false,
      "faits_retenus": ["ID_34", "ID_42"],
      "briefs_recherche_additionnelle": []
    },
    {
      "numero": 14,
      "type": "Vestige_Majeur",
      "titre_etape": "Saint-Germain-des-Prés : La Seigneurie dans la Ville",
      "localisation": "Place Saint-Germain-des-Prés, 75006 Paris. Positionnez-vous devant le clocher roman, côté place.",
      "transition_vers_suivant": "Prenez la rue Bonaparte vers le nord jusqu'au quai, puis traversez la Seine par le Pont du Carrousel — le Louvre est en face, et sous sa Cour Carrée dorment les vestiges de la tour de Philippe Auguste.",
      "consigne_plume": "Regardez le clocher roman du XIe siècle : c'est l'un des rares volumes médiévaux encore debout à Paris, et il appartient à une abbaye qui était une seigneurie indépendante avec ses propres serfs, sa propre justice, sa propre foire et ses propres conflits avec l'évêque de Paris. Élargissez sur l'abbaye comme modèle de la fragmentation du pouvoir médiéval : l'abbé levait des taxes sur les marchands de la foire Saint-Germain attestée dès 1176, détenait des serfs sur ses terres documentés dans le polyptyque d'Irminon, et quand les abbés commendataires du XVe siècle comme Charles de Bourbon ont commencé à percevoir personnellement les revenus sans remplir leurs obligations monastiques, c'est toute la logique de l'institution qui s'est effondrée de l'intérieur — le palais abbatial qu'il a fait construire en 1586 est encore visible rue de l'Abbaye.",
      "cible_duree_audio": "3 minutes",
      "is_grand_format": false,
      "faits_retenus": ["ID_58", "ID_59", "ID_60", "ID_61"],
      "briefs_recherche_additionnelle": []
    },
    {
      "numero": 15,
      "type": "Vestige_Majeur",
      "titre_etape": "Sous-Sol du Louvre : La Tour de Philippe Auguste",
      "localisation": "Musée du Louvre, entrée par la Pyramide, 75001 Paris. Les vestiges médiévaux sont accessibles dans la salle basse du niveau -1, aile Sully.",
      "transition_vers_suivant": "Ressortez du Louvre et prenez la rue de Rivoli vers l'est, puis le boulevard Morland vers le sud-est jusqu'à la Place de la Bastille — comptez 25 minutes à pied ou prenez le métro ligne 1 jusqu'à Bastille.",
      "consigne_plume": "Regardez les fondations circulaires de la tour : vous êtes dans le donjon original de Philippe Auguste, construit vers 1190 comme symbole de domination sur une ville qu'il ne contrôlait pas encore totalement — Ferrand de Flandre, capturé à Bouvines en 1214, y a été enfermé pendant 13 ans. Élargissez sur l'enceinte de Philippe Auguste comme acte politique fondateur : construire un mur autour de Paris en 1190-1215, c'est définir pour la première fois ce qu'est 'Paris' — et tout ce qui est laissé dehors, comme les tanneries de la Bièvre et les arènes de Lutèce, est condamné à l'invisibilité juridique et fiscale pendant des siècles.",
      "cible_duree_audio": "2 minutes",
      "is_grand_format": false,
      "faits_retenus": ["ID_27", "ID_28"],
      "briefs_recherche_additionnelle": []
    },
    {
      "numero": 16,
      "type": "Vestige_Majeur",
      "titre_etape": "Place de la Bastille : Là Où Marcel a Été Tué",
      "localisation": "Place de la Bastille, 75004 Paris. Positionnez-vous au pied de la Colonne de Juillet — elle est plantée exactement sur l'emplacement de la Porte Saint-Antoine médiévale.",
      "transition_vers_suivant": null,
      "consigne_plume": "Regardez la base de la Colonne de Juillet : vous êtes à l'emplacement exact de la Porte Saint-Antoine, où Étienne Marcel a été abattu le 31 juillet 1358 par Jean Maillart et ses partisans alors qu'il s'apprêtait à livrer les clés de Paris aux troupes de Charles le Mauvais. Élargissez sur la révolte de Marcel comme moment où Paris a failli devenir une commune autonome : en février 1358, Marcel avait fait assassiner deux maréchaux royaux dans la chambre même du Dauphin au Palais de la Cité et contraint Charles V à porter le chaperon rouge et bleu de Paris — une humiliation du pouvoir royal documentée dans les Grandes Chroniques — avant de s'allier avec les Jacques insurgés ruraux dans une coalition bourgeoisie-paysans qui aurait pu recomposer l'ordre politique français ; son assassinat a tout refermé, et la statue qui lui a été érigée devant l'Hôtel de Ville au XIXe siècle est une récupération républicaine tardive d'un homme que ses propres partisans ont trahi.",
      "cible_duree_audio": "4 minutes",
      "is_grand_format": false,
      "faits_retenus": ["ID_52", "ID_53", "ID_54", "ID_55", "ID_43"],
      "briefs_recherche_additionnelle": []
    }
  ],
  "fils_narratifs": [
    {
      "theme": "La Prédation Capétienne : Juifs, Templiers, Clergé",
      "introduit_au": 1,
      "developpe_aux": [3, 7, 13],
      "clos_au": 16,
      "resume": "Le Palais de la Cité comme quartier général de la confiscation : expulsion des Juifs 1182 et conversion de leur synagogue -> cycle d'extorsion institutionnalisé (1182, 1306, 1315, 1323, 1394) -> arrestation secrète des Templiers 1307 depuis le même palais, torture, dissolution sans procès équitable -> bûcher de Molay 1314 et malédiction dynastique réelle (extinction des Capétiens directs 1314-1328) -> la violence d'État médiévale n'est pas une exception, c'est le moteur fiscal du royaume."
    },
    {
      "theme": "Le Pouvoir Contre la Ville : De Marcel à Charles V",
      "introduit_au": 6,
      "developpe_aux": [8, 9],
      "clos_au": 16,
      "resume": "La Grève comme base du contre-pouvoir marchand sous Marcel (1356-1358) -> meurtre des maréchaux au Palais de la Cité, humiliation de Charles V -> alliance tactique avec les Jacques et les Bourguignons -> assassinat de Marcel porte Saint-Antoine -> Charles V répond en construisant l'enceinte asymétrique (rive droite seulement) et en faisant de Vincennes son bunker dynastique hors de Paris : la ville est trop dangereuse pour le roi."
    },
    {
      "theme": "Les Institutions Contre l'Évêque",
      "introduit_au": 2,
      "developpe_aux": [10, 11],
      "clos_au": 14,
      "resume": "Louis IX court-circuite Notre-Dame via la bulle d'exemption épiscopale de 1244 pour la Sainte-Chapelle -> l'Université obtient la même indépendance en 1231 (Parens Scientiarum) et condamne ses propres maîtres (Siger de Brabant, 1277) -> l'abbaye de Sainte-Geneviève exclut l'évêque de la consécration de son chœur en 1163 -> Saint-Germain-des-Prés fonctionne comme seigneurie indépendante avec justice propre : le Paris médiéval est un archipel de juridictions rivales, pas une ville unifiée."
    }
  ]
}
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

    def get_text(self, content, system_prompt="", research_block_1="", research_block_2="", plan="", temperature=1, cache = False, messages_history=[]):
        # synchronous http call, wait for the full text to be generated
        try:
            logger.info("Avant appel claude")

            system_block = self.get_system_block(system_prompt, research_block_1, research_block_2, plan)
            # save_LLM_output(system_block, "System_block")

            # logger.debug(f"content : {content}")
            messages_history.append({"role": "user", "content": content})

            api_param = {
                "max_tokens": 16384,
                "system": system_block,
                "temperature": temperature,
                "messages": messages_history,
                "model": "claude-sonnet-4-6",
            }
            if cache:
                api_param["cache_control"] = {"type": "ephemeral"}

            logger.debug(f"Claude system_block : {system_block}")
            logger.debug(f"Claude messages_history : {messages_history}")
            response = self.client.messages.create(**api_param)
            logger.info("Après appel claude")
            logger.debug(response)

            return response.content[0].text
        except Exception as e:
            logger.error(f"Claude [Error]: {e}")
            save_LLM_output(response, "Claude_Sonnet_4_6")