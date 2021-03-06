# coding: utf-8
import hashlib
import random
#import smtplib
#from email.mime.multipart import MIMEMultipart
#from email.mime.text import MIMEText
from flask import *

import config
import sql

app = Flask(__name__, static_url_path='')
days = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"]

n_par_page = 4


# Page d'accueil qui redirige vers la page de recherche ou page de login
@app.route('/')
def index():
	"""Page d'accueil qui redirige vers la page de recherche ou page de login"""
	sql_obj = sql.MysqlObject()
	if check_connexion():
		mail = session['mail']
		admin_user = check_admin()

	# STATS
	nbr_users = sql_obj.stat_nombre()
	offres = sql_obj.stat_offres()
	demandes = sql_obj.stat_demandes()

	return render_template("accueil.html", **locals())


# Page de connexion
@app.route('/login', methods=['GET'])
def connexion():
	"""Page de connexion"""
	sql_obj = sql.MysqlObject()
	if check_connexion():
		return redirect(url_for('recherche',
								info_msg="Vous êtes connecté, vous pouvez dès à présent accéder au"
										 " service de tutorat."))
	else:
		if request.args.get('info_msg'):
			info_msg = request.args.get('info_msg')
		return render_template("authentification/connexion.html", **locals())


# Page de connexion
@app.route('/login', methods=['POST'])
def traitement_connexion():
	"""Compare les données rentré par l'utilisateur à celles de la BDD et nous connect si les données correspondent"""
	# Traitement du formulaire envoyé par l'utilisteur depuis la page login
	sql_obj = sql.MysqlObject()
	if not check_connexion():
		# obtenir les données entrées par l'utilisateur
		mail = request.form.get('mail')
		mdp = request.form.get('mdp')
		# chiffrer le mot de passe
		mdp_chiffre = hashlib.sha256(str(mdp).encode('utf-8')).hexdigest()
		# comparer les infos à celle de la base de données
		if sql_obj.mail_in_bdd(mail):
			if sql_obj.get_user_info(mail).mdp == mdp_chiffre:
				if not sql_obj.check_ban(mail):
					session['mail'] = mail
					return redirect(url_for('recherche',
											info_msg="Vous êtes connecté, vous pouvez dès à présent accéder au service"
													 " de tutorat."))
				else:
					return redirect(url_for('connexion',
											info_msg="Vous êtes banni de cette platforme. Veuillez contacter un"
													 " documentaliste."))
			else:
				return redirect(url_for('connexion',
										info_msg="Erreur lors de la connexion, veuillez vérifier les informations"
												 " saisies puis réessayez."))
		elif sql_obj.mail_in_register(mail):
			return redirect(
				url_for("confirm_register_get", mail=mail, info_msg="Veuillez finaliser votre inscription."))
		else:
			return redirect(url_for('connexion',
									info_msg="Aucun compte ne correspond à l'adresse email renseignée."))
	else:
		return redirect(url_for('recherche',
								info_msg="Vous êtes connecté, vous pouvez dès à présent accéder au"
										 " service de tutorat."))


# Page d'inscription
@app.route('/register', methods=['GET'])
def inscription():
	"""Page d'inscription"""
	sql_obj = sql.MysqlObject()
	if not check_connexion():
		if request.args.get('info_msg'):
			info_msg = request.args.get('info_msg')
		return render_template("authentification/inscription.html", classes=sql_obj.classes_liste(), **locals())
	else:
		return page_recherche()


@app.route('/register', methods=['POST'])
def traitement_inscription():
	"""Envoie les données rentrées par l'utilisateur à la BDD pour l'inscrire"""
	sql_obj = sql.MysqlObject()
	classes = sql_obj.classes_liste()
	if not check_connexion():
		if not sql_obj.mail_in_bdd(request.form['mail']) and not sql_obj.mail_in_register(request.form['mail']):
			# Vérification que la classe est valide
			if request.form.get('classe') in classes:
				# Chiffrement du mdp
				chaine_mot_de_passe = request.form.get('mdp')
				mdp_confirm = request.form.get('mdp2')
				if chaine_mot_de_passe == mdp_confirm:
					mot_de_passe_chiffre = hashlib.sha256(str(chaine_mot_de_passe).encode('utf-8')).hexdigest()
					nom = request.form.get('prenom') + ' ' + request.form.get('nom')
					mail = request.form.get('mail')
					classe = request.form.get('classe')
					code = "000000"
					sql_obj.create_compte_validate(nom, mot_de_passe_chiffre, mail,
												   classe, code)

					return redirect(url_for("confirm_register_get", C=True, mail=mail))

				else:
					return render_template("authentification/inscription.html",
										   info_msg='Les mots de passe ne correspondent pas.', **locals())
			else:
				return render_template("authentification/inscription.html",
									   info_msg='Votre classe n\'est pas valide', **locals())
		else:
			return redirect(url_for('inscription',
									info_msg="Cette adresse email existe déjà"))
	else:
		return page_recherche()


# Confirmation inscription (affichage initial + renvoie du code)
@app.route('/register/confirm', methods=['GET'])
def confirm_register_get():
	"""Page confirmation d'inscription"""
	sql_obj = sql.MysqlObject()
	if request.args.get('mail'):
		mail = request.args.get('mail')
	else:
		return redirect(url_for("inscription"))

	if request.args.get('info_msg2'):
		info_msg2 = request.args.get('info_msg2')
	else:
		info_msg2 = ""

	if request.args.get('C'):
		# Génération du code
		element = "0123456789"
		code = ""
		for i in range(6):
			code = code + element[random.randint(0, 9)]
		# Envoi de l'email
		u = objects.Utilisateur(["candidat", "", mail, "", 0, 0])
		u.notifier("Code de validation",
					"Bonjour,\n\nVoici le code de validation de votre inscription : " \
				  + code + "\nL\'équipe de BlaBla-Tutorat vous souhaite une bonne journée.\n\n\n\n\n" \
						   "Cet e-mail a été généré automatiquement, merci de ne pas y répondre." \
						   " Pour toute question, veuillez vous adresser aux documentalistes.")
		#msg = MIMEMultipart()
		#msg['From'] = config.email
		#msg['To'] = mail
		#msg['Subject'] = 'BlaBla-Tutorat -- Code de validation'
		#message = 
		#msg.attach(MIMEText(message))
		#mailserver = smtplib.SMTP(config.smtp, config.smtp_port)
		#mailserver.starttls()
		#mailserver.login(config.email, config.email_password)
		#mailserver.sendmail(msg['From'], msg['To'], msg.as_string())
		#mailserver.quit()
		
		sql_obj.code_update(code, mail)
		if info_msg2 != "":
			return redirect(url_for("confirm_register_get", mail=mail, info_msg2=info_msg2))
		else:
			return redirect(url_for("confirm_register_get", mail=mail))

	info = sql_obj.info_register(mail)
	if len(info) > 0:
		nom = info[0][0]
		mdp = info[0][1]
		mail = info[0][2]
		classe = info[0][3]
		code = info[0][4]
		return render_template("authentification/verification.html", **locals())
	else:
		return redirect(url_for("inscription"))


# Confirmation inscription (vérification code)
@app.route('/register/confirm', methods=['POST'])
def confirm_register_post():
	"""Page confirmation d'inscription"""
	sql_obj = sql.MysqlObject()

	if request.form.get('code_V') == request.form.get('code'):
		# Envoi des infos à la base de données
		sql_obj.delete_register(request.form.get('mail'))
		sql_obj.create_compte(request.form.get('nom'), request.form.get('mdp'), request.form.get('mail'),
							  request.form.get('classe'))
		return redirect(url_for("connexion",
								info_msg="Votre compte a bien été créé,\n"
										 "vous pouvez dès à présent vous connecter"))
	else:
		return redirect(
			url_for("confirm_register_get", C=True, mail=request.form.get('mail'),
					info_msg2="Vous n'avez pas tapé le bon code. Un nouveau vous a été envoyé par mail."))


# Annuler l'inscription
@app.route('/del_register', methods=['GET', 'POST'])
def del_register():
	"""Annuler l'inscription"""
	sql_obj = sql.MysqlObject()
	if request.args.get('mail'):
		mail = request.args.get('mail')
		if sql_obj.mail_in_register(mail):
			sql_obj.delete_register(mail)
			return redirect(
				url_for("connexion", info_msg="Vous avez bien annulé votre inscription sur BlaBla-Tutorat."))
		else:
			abort(404)
	else:
		abort(404)


# Mot de passe oublié
@app.route('/forgot', methods=['GET'])
def mdp_oublie():
	"""Page de mot de passe oublié"""
	if not check_connexion():
		if request.args.get('info_msg'):
			info_msg = request.args.get('info_msg')
		# Vérification configuration complète
		if config.email != "" and config.email_password != "":
			return render_template("authentification/mdp_oublie.html", **locals())
		else:
			return redirect(url_for('connexion', info_msg="Veuillez vous adresser directement aux documentalistes."))
	else:
		return page_recherche()


# Traitement Mot de passe oublié
@app.route('/forgot', methods=['POST'])
def traitement_mdp_oublie():
	""" Créé un nouveau mot de passe aléatoirement
		et l'envoie par mail à l'utilisateur
	"""
	sql_obj = sql.MysqlObject()
	if not check_connexion():
		mail = request.form['mail']
		if sql_obj.mail_in_bdd(mail):
			user = sql_obj.get_user_info(mail)
			# Génération nouveau mot de passe
			element = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+-*/~$%&.:?!"
			passwd = ""
			for i in range(12):
				passwd = passwd + element[random.randint(0, 73)]

			# Chiffrement du nouveau mot de passe
			passwd_hash = hashlib.sha256(str(passwd).encode('utf-8')).hexdigest()

			# Envoi du nouveau mot de passe à la base de données
			sql_obj.modify_user_info_mdp(request.form['mail'], passwd_hash)

			# Envoi de l'email
			user.notifier('BlaBla-Tutorat -- Nouveau mot de passe',
							'Bonjour,\n\nNous avons généré pour vous un nouveau mot de passe : ' \
							+ passwd + '\nVeuillez le changer dès que vous vous connecterez à BlaBla-Tutorat.\n' \
							'L\'équipe de BlaBla-Tutorat vous souhaite une bonne journée.\n\n\n\n\nCet e-mail' \
							' a été généré automatiquement, merci de ne pas y répondre.' \
							' Pour toute question, veuillez vous adresser aux documentalistes.')

			return redirect(url_for('connexion', info_msg="Un nouveau mot de passe vous a été envoyé."))
		else:
			return redirect(url_for("mdp_oublie", info_msg="Cette adresse e-mail ne correspond à aucun compte"))
	else:
		return page_recherche()


# Page de Profil info utilisateur
@app.route('/stat')
def stat():
	"""Page de de profil avec les informations de l'utilisateur"""
	sql_obj = sql.MysqlObject()

	if check_connexion():
		mail = session['mail']
		admin_user = check_admin()
		user = sql_obj.get_user_info(mail).nom

	if request.args.get('info_msg'):
		info_msg = request.args.get('info_msg')

	filieres = sql_obj.filieres_liste()
	matieres = sql_obj.matieres_liste()
	offres = sql_obj.get_all_offres()
	demandes = sql_obj.get_all_demandes()
	t = []
	for m in matieres:
		l = []
		t.append(l)
		for f in filieres:
			c = [[], []]
			l.append(c)
			i = 0
			while i < len(offres):
				o = offres[i]
				if o.filiere == f and o.matiere == m:
					c[0].append(o)
					del offres[i]
				else:
					i += 1

			i = 0
			while i < len(demandes):
				d = demandes[i]
				if sql_obj.get_class_level(d.classe) == sql_obj.get_filiere_level(f) and d.matiere == m:
					c[1].append(d)
					del demandes[i]
				else:
					i += 1

	return render_template("statistiques.html", **locals())


# Page de Profil info utilisateur connecté
@app.route('/profile/view')
def profil():
	"""Page de de profil avec les informations de l'utilisateur"""
	sql_obj = sql.MysqlObject()
	if request.args.get('delete'):
		delete_account = request.args.get('delete')
	if check_connexion():
		mail = session['mail']
		admin_user = check_admin()
		user = sql_obj.get_user_info(mail).nom
		if request.args.get('info_msg'):
			info_msg = request.args.get('info_msg')
		return render_template("profil/profil_u.html", 
								infos = sql_obj.get_user_info(mail), 
								days=days, **locals())
	else:
		# Redirection si l'utilisateur n'est pas connecté
		return page_connexion()


# Page de Profil
@app.route('/profile/tutorials')
def profil_2():
	"""Page de profil avec la liste des offres et des demandes créées par l'utilisateur"""
	sql_obj = sql.MysqlObject()
	if check_connexion():
		mail = session['mail']
		admin_user = check_admin()
		user = sql_obj.get_user_info(mail).nom
		demandes = sql_obj.get_user_demandes(mail)
		demandes_t = sql_obj.get_user_demandes_tuteur(mail)
		if request.args.get('info_msg'):
			info_msg = request.args.get('info_msg')
		return render_template("profil/profil_t_p.html", offres_creees=sql_obj.get_user_offres(mail),
							   offres_suivies=sql_obj.get_user_offres_suivies(mail), days=days, **locals())
	else:
		# Redirection si l'utilisateur n'est pas connecté
		return page_connexion()


# Page de suppression Profil
@app.route('/profile/delete')
def profil_3():
	"""Supprime le compte utilisateur de la BDD"""
	sql_obj = sql.MysqlObject()
	if check_connexion():
		mail = session['mail']
		sql_obj.delete_account(mail)
		liste = sql_obj.get_user_offres_suivies(mail)
		for x in liste:
			sql_obj.delete_participant(x.id, mail)
		return redirect(url_for('connexion', info_msg="Votre compte a bien été supprimé."))
	else:
		# Redirection si l'utilisateur n'est pas connecté
		return page_connexion()


# Page de profil d'un utilisateur
@app.route('/profile/view/<mail>')
def profil_4(mail):
	"""Popup avec les informations de l'utilisateur qui correspond au mail cliqué"""
	sql_obj = sql.MysqlObject()
	if check_connexion():
		if sql_obj.mail_in_bdd(mail):
			return render_template("profil/profil_visit.html", 
									infos=sql_obj.get_user_info(mail), 
									**locals())
		else:
			return render_template("error.html", 
									message="Erreur - Cet utilisateur n'existe pas",
								   **locals())
	else:
		# Redirection si l'utilisateur n'est pas connecté
		return page_connexion()


# Page de modification du profil
@app.route('/profile/update', methods=['GET', 'POST'])
def profil_update():
	"""Page de mise à jour de profil, récolte les information données par l'utilisateur et les envoie à la BDD"""
	sql_obj = sql.MysqlObject()
	if check_connexion():
		if request.args.get('info_msg'):
			info_msg = request.args.get('info_msg')
		mail = session['mail']
		admin_user = check_admin()
		classes = sql_obj.classes_liste()
		if len(request.form) == 0:
			# Pas de formulaire envoyé, on charge la page normalement
			return render_template("profil/profil_update.html", infos=sql_obj.get_user_info(mail), **locals())
		else:
			if request.form.get('classe') in classes:
				# Chiffrement du mdp
				if request.form.get('mdp') != '':
					if hashlib.sha256(str(request.form.get('mdp')).encode('utf-8')).hexdigest() == \
							sql_obj.get_user_info(mail).nom:
						if request.form.get('mdp1') != '' and request.form.get('mdp2') != '':
							chaine_mot_de_passe = request.form.get('mdp1')
							mdp_confirm = request.form.get('mdp2')
							if chaine_mot_de_passe == mdp_confirm:
								mot_de_passe_chiffre = hashlib.sha256(
									str(chaine_mot_de_passe).encode('utf-8')).hexdigest()
								# Envoi des infos à la base de données
								sql_obj.modify_user_info_mdp(mail, mot_de_passe_chiffre)
							else:
								return redirect(url_for("profil_update",
														info_msg="Erreur - Vous n'avez pas correctement confirmé votre"
																 " nouveau mot de passe."))
						else:
							return redirect(url_for(
								"profil_update", info_msg="Erreur - Vous n'avez pas rentré de nouveau mot de passe."))
					else:
						return redirect(url_for("profil_update",
												info_msg="Erreur - Veuillez vérifier votre ancien mot de passe."))
				# Envoi des infos à la base de données
				sql_obj.modify_user_info(mail, request.form.get('classe'))
				return redirect(url_for("profil", info_msg="Votre profil a bien été modifié."))
			else:
				return render_template("error.html", message="Erreur - Veuillez vérifier les champs du formulaire",
									   **locals())
	else:
		# Redirection si l'utilisateur n'est pas connecté
		return page_connexion()


# Page d'Administration offres en courts
@app.route('/admin/tutorials/progress', methods=['GET', 'POST'])
def admin_oc():
	"""Page d'administration qui affiche les offres en cours"""
	sql_obj = sql.MysqlObject()
	if check_connexion():
		mail = session['mail']
		admin_user = check_admin()
		user = sql_obj.get_user_info(mail).nom
		if admin_user:
			if request.args.get('info_msg'):
				info_msg = request.args.get('info_msg')
			if request.form.get("user_search"):
				user_search = request.form.get("user_search")
				user_search_liste = sql_obj.get_user_info_pseudo(user_search)
				if len(user_search_liste) == 1:
					# Un utilisateur a été trouvée
					return render_template("admin/admin_t_p.html",
										   tutorats_actifs=sql_obj.offres_liste_tri_admin(user_search_liste[0].mail),
										   days=days, **locals())
				else:
					# Pas d'utilisateur trouvé donc liste vide
					return render_template("admin/admin_t_p.html", tutorats_actifs=[], days=days,
										   **locals())
			else:
				return render_template("admin/admin_t_p.html", tutorats_actifs=sql_obj.offres_liste_validees(),
									   days=days, **locals())
		else:
			abort(403)
	else:
		return redirect(url_for("connexion", info_msg='Connectez vous avant de continuer.'))


# Page d'Administration demandes en courts
@app.route('/admin/tutorials/progress/demandes', methods=['GET', 'POST'])
def admin_oc2():
	"""Page d'administration qui affiche les demandes en cours"""
	sql_obj = sql.MysqlObject()
	if check_connexion():
		mail = session['mail']
		admin_user = check_admin()
		user = sql_obj.get_user_info(mail).nom
		if admin_user:
			if request.args.get('info_msg'):
				info_msg = request.args.get('info_msg')
			if request.form.get("user_search"):
				user_search = request.form.get("user_search")
				user_search_liste = sql_obj.get_user_info_pseudo(user_search)
				if len(user_search_liste) == 1:
					# Un utilisateur a été trouvée
					return render_template("admin/admin_t_p_d.html",
										   demandes=sql_obj.demandes_liste_tri_admin(user_search_liste[0].mail),
										   days=days, **locals())
				else:
					# Pas d'utilisateur trouvé donc liste vide
					return render_template("admin/admin_t_p_d.html", demandes=[], days=days,
										   **locals())
			else:
				return render_template("admin/admin_t_p_d.html", demandes=sql_obj.demandes_liste_validees(),
									   days=days, **locals())
		else:
			abort(403)
	else:
		return redirect(url_for("connexion", info_msg='Connectez vous avant de continuer.'))


# Page d'Administration offres à valider
@app.route('/admin/tutorials/validate')
def admin_ov():
	"""Page d'administration qui affiche les offres et demandes à valider"""
	sql_obj = sql.MysqlObject()
	if check_connexion():
		mail = session['mail']
		admin_user = check_admin()
		user = sql_obj.get_user_info(mail).nom
		if admin_user:
			if request.args.get('info_msg'):
				info_msg = request.args.get('info_msg')
			if request.args.get('reset_msg'):
				reset_msg = request.args.get('reset_msg')
			return render_template("admin/admin_t_v.html", offres_V=sql_obj.offres_liste_valider(),
								   demandes_V=sql_obj.demandes_liste_valider(), days=days,
								   **locals())
		else:
			abort(403)
	else:
		return redirect(url_for("connexion", info_msg='Connectez vous avant de continuer.'))


# Page d'Administration profile utilisateur
@app.route('/admin/users', methods=['GET', 'POST'])
def admin_u():
	"""Page d'administration qui affiche la liste des utilisateurs du site"""
	sql_obj = sql.MysqlObject()
	if check_connexion():
		mail = session['mail']
		admin_user = check_admin()
		user_search = ""
		user = sql_obj.get_user_info(mail).nom
		if admin_user:
			if request.args.get('info_msg'):
				info_msg = request.args.get('info_msg')
			if request.form.get("user_search"):
				user_search = request.form.get("user_search")
				return render_template("admin/admin_u.html", 
									   user_list=sql_obj.get_user_info_pseudo(user_search),
									   tutorats_actifs=sql_obj.offres_liste_validees(),
									   demandes=sql_obj.demandes_liste_validees(), days=days, **locals())
			else:
				return render_template("admin/admin_u.html", 
									   user_list=sql_obj.liste_user(),
									   tutorats_actifs=sql_obj.offres_liste_validees(),
									   demandes=sql_obj.demandes_liste_validees(), days=days, **locals())
		else:
			abort(403)
	else:
		return redirect(url_for("connexion", info_msg='Connectez vous avant de continuer.'))


# Page de recherche d'offres
@app.route('/search', methods=['GET', 'POST'])
def recherche():
	"""Page de recherche"""
	sql_obj = sql.MysqlObject()

	if check_connexion():
		mail = session['mail']
		admin_user = check_admin()
		user = sql_obj.get_user_info(mail).nom

		# Nombre d'éléments par page
		npp = request.form.get('n_p_page')
		if npp is None:
			npp = n_par_page


		# Message
		if request.args.get('info_msg'):
			info_msg = request.args.get('info_msg')

		# Numéro de la page à afficher
		if request.form.get('precedent'):
			page = int(request.form.get('page')) - 1
		elif request.form.get('suivant'):
			page = int(request.form.get('page')) + 1
		else:
			page = 0

		type_obj = request.form.get("categorie")
		if type_obj == "demande":
			# PARTIE DEMANDES
			matieres = sql_obj.liste_dispo('matiere', 'demandes', admin_user)
			
			option = request.form.get("option")
			option2 = request.form.get("option2")
			

			if option == "suggestion":
				suggest_d1 = sql_obj.get_tuteur_info(mail)[0]
				suggest_d2 = sql_obj.get_tuteur_info(mail)[1]
				return render_template("suggestion/suggest_d.html", days=days, **locals())

			else:
				lst = sql_obj.liste_demandes(mail, option, option2)
				npages = (len(lst) - 1) // npp + 1
				return render_template("recherche/recherche_demande.html",
									   demandes=lst[page * npp:(page + 1) * npp],
									   days=days, **locals())

		else:
			# PARTIE OFFRES
			matieres = sql_obj.liste_dispo('matiere', 'offres', admin_user)
			filieres = sql_obj.liste_dispo('filiere', 'offres', admin_user)
			
			option = request.form.get("option")
			option2 = request.form.get("option2")
			
				
			if option == "suggestion":
				suggest_o1 = sql_obj.get_tutore_info(mail)[0]
				suggest_o2 = sql_obj.get_tutore_info(mail)[1]
				return render_template("suggestion/suggest_o.html",
									   days=days, **locals())

			else:
				lst = sql_obj.liste_offres(mail, option, option2)
				npages = (len(lst) - 1) // npp + 1
				return render_template("recherche/recherche_offre.html",
									   offres=lst[page * npp:(page + 1) * npp],
									   days=days, **locals())

	else:
		# Redirection si l'utilisateur n'est pas connecté
		return page_connexion()


# Affichage du formulaire de création d'une offre
@app.route('/create', methods=['GET'])
def creation():
	"""Page de création"""
	sql_obj = sql.MysqlObject()
	if check_connexion():
		mail = session['mail']
		admin_user = check_admin()
		user = sql_obj.get_user_info(mail).nom
		return render_template("creation/creation.html", 
								filieres=sql_obj.filieres_liste(),
							   matieres=sql_obj.matieres_liste(), 
							   days=days, **locals())
	else:
		# Redirection si l'utilisateur n'est pas connecté
		return page_connexion()


# Traitement du formulaire + upload bdd
@app.route('/create', methods=['POST'])
def traitement_creation():
	"""Envoie les données rentrées par l'utilisateur à la BDD"""
	# On ne traite pas la demande dans le doute ou l'élève n'a pas renseigné de créneau horaire
	process = False
	sql_obj = sql.MysqlObject()
	if check_connexion():
		mail = session['mail']
		admin_user = check_admin()
		user = sql_obj.get_user_info(mail).nom

		if len(request.form) == 1:
			# Changement offre/demande
			if request.form['categorie'] == "demande":
				# On definit la catégorie sur demande
				demande = True
				classe = sql_obj.get_user_info(mail).classe
				return render_template("creation/creation.html", filieres=sql_obj.filieres_liste(),
									   matieres=sql_obj.matieres_liste(),
									   days=days, **locals())
			else:
				# Sinon on charge la template de base
				return render_template("creation/creation.html", filieres=sql_obj.filieres_liste(),
									   matieres=sql_obj.matieres_liste(),
									   days=days, **locals())
		else:
			# Suite du formulaire de création
			horaires = request.form["horaires_data"]
			if len([c for c in horaires if c == '1']) > 0:
				process = True

			if process:
				# Création
				filieres = sql_obj.filieres_liste()
				matieres = sql_obj.matieres_liste()
				if request.form.get("filiere"):
					# OFFRE
					if request.form.get("filiere") in filieres and request.form.get("matiere") in matieres:
						sql_obj.create_offre(mail, request.form.get('filiere'),
											 request.form.get('matiere'),
											 horaires)
						return redirect(url_for("recherche",
												info_msg="Votre offre a bien été créée. Elle est actuellement"
														 " en attente de validation."))
					else:
						return render_template("error.html",
											   message="Erreur - Veuillez vérifier les champs du formulaire",
											   **locals())
				else:
					# DEMANDE
					if request.form.get("matiere") in matieres:
						sql_obj.create_demande(mail, request.form.get('classe'),
											   request.form.get('matiere'),
											   horaires)
						return redirect(url_for("recherche",
												info_msg="Votre demande a bien été créée. Elle est actuellement"
														 " en attente de validation."))
					else:
						return render_template("error.html",
											   message="Erreur - Veuillez vérifier les champs du formulaire",
											   **locals())
			else:
				# Erreur
				return render_template("error.html", message="Erreur - Veuillez renseigner au moins un horaire",
									   **locals())
	else:
		# Redirection si l'utilisateur n'est pas connecté
		return page_connexion()


# Page d'enregistrement (s'enregistrer en tant que participant)
@app.route('/apply', methods=['POST'])
def enregistrement():
	"""Enregistre l'utilisateur comme participant à ce tutorat"""
	sql_obj = sql.MysqlObject()
	if check_connexion():
		mail = session['mail']

		if request.form.get("categorie") == "demande":
			result_code = sql_obj.add_tuteur(request.form.get("id"), mail)
		else:
			result_code = sql_obj.add_participant(request.form.get("id"), mail)

		if result_code == 0:
			# Pas d'erreur
			if request.form.get("categorie") == "demande":
				return redirect(url_for("select_2", tutorat_id=request.form.get("id")))
			else:
				return redirect(url_for("select", tutorat_id=request.form.get("id")))
		
		elif result_code == 1:
			# Erreur l'utilisateur participe déjà à l'offre
			return redirect(url_for("recherche", info_msg="Vous vous êtes déjà enregistré pour ce Tutorat"))
		
		elif result_code == 2:
			# Erreur (cas très rare ou l'utilisateur accepte une offre qui est déjà pleine)
			return redirect(url_for("recherche", info_msg="Ce Tutorat est déjà plein"))
		
		elif result_code == 3:
			# Erreur l'utilisateur veut participer à une offre qu'il a créée
			return redirect(url_for("recherche", info_msg="Vous êtes l'auteur de ce tutorat"))
		
		elif result_code == 4:
			# Erreur l'utilisateur n'est pas dans la même classe que le premier participant
			return redirect(
				url_for("recherche", info_msg="Vous n'appartenez pas à la même classe que le premier participant"))
	else:
		# Redirection si l'utilisateur n'est pas connecté
		return page_connexion()


# Selection horaires (offre)
@app.route('/select', methods=['GET', 'POST'])
def select():
	"""Selection des horaires pour les offres"""
	if check_connexion():
		mail = session['mail']
		sql_obj = sql.MysqlObject()
		user = sql_obj.get_user_info(mail).nom
		admin_user = check_admin()
		
		if request.args.get('tutorat_id'):
			id_offre = request.args.get('tutorat_id')

			if mail == sql_obj.get_offre(id_offre).participant:
				return render_template("selection/select_horaires.html", 
										o=sql_obj.get_offre(id_offre), days=days,
									   **locals())
			elif mail == sql_obj.get_offre(id_offre).participant2:
				return redirect(
					url_for("recherche", 
							info_msg="Vous avez bien été ajouté en tant que participant à ce tutorat."))
			else:
				abort(403)

		elif len(request.form) != 0:
			horaires = request.form["horaires_data"]
			sql_obj.modifier_offre(mail, request.form.get("id"), horaires)
			return redirect(
				url_for("recherche", 
						info_msg="Vous avez bien été ajouté en tant que participant à ce tutorat."))

		else:
			abort(403)

	else:
		return page_connexion()


# Selection horaires (demande)
@app.route('/select_2', methods=['GET', 'POST'])
def select_2():
	"""Selection des horaires pour les demandes"""
	if check_connexion():
		mail = session['mail']
		sql_obj = sql.MysqlObject()
		user = sql_obj.get_user_info(mail).nom
		admin_user = check_admin()
		if request.args.get('tutorat_id'):
			id_demande = request.args.get('tutorat_id')

			if mail == sql_obj.get_demande(id_demande).tuteur:
				return render_template("selection/select_horaires_d.html", o=sql_obj.get_demande(id_demande), days=days,
									   **locals())
			else:
				abort(403)

		elif len(request.form) != 0:
			horaires = request.form["horaires_data"]
			sql_obj.modifier_demande(request.form.get("id"), horaires)
			return redirect(url_for("recherche", info_msg="Vous avez bien été ajouté en tant que tuteur."))

		else:
			abort(403)

	else:
		return page_connexion()


# Modification d'une demande (affichage)
@app.route('/edit_d')
def modifier_demande():
	"""Modification d'une demande"""
	if check_connexion():
		mail = session['mail']
		if request.args.get('id'):
			sql_obj = sql.MysqlObject()
			admin_user = check_admin()
			demande_id = request.args.get('id')
			# Vérification que l'auteur est celui qui demande la suppression
			if mail == sql_obj.get_demande(demande_id).auteur:
				return render_template("edit/edit_d.html", demande=sql_obj.get_demande(demande_id),
									   filieres=sql_obj.filieres_liste(), matieres=sql_obj.matieres_liste(),
									   days=days, **locals())
			else:
				abort(403)
		else:
			abort(403)

	else:
		return page_connexion()


# Modification d'une offre (affichage)
@app.route('/edit_o')
def modifier_offre():
	"""Modification d'une offre"""
	if check_connexion():
		mail = session['mail']
		if request.args.get('id'):
			sql_obj = sql.MysqlObject()
			admin_user = check_admin()
			offre_id = request.args.get('id')
			# Vérification que l'auteur est celui qui demande la suppression
			if mail == sql_obj.get_offre(offre_id).auteur:
				return render_template("edit/edit_o.html", offre=sql_obj.get_offre(offre_id),
									   filieres=sql_obj.filieres_liste(), matieres=sql_obj.matieres_liste(),
									   days=days, **locals())
			else:
				abort(403)
		else:
			abort(403)

	else:
		return page_connexion()


# Modification d'une offre/demande (formulaire)
@app.route('/edit_apply', methods=['POST'])
def modification_offre_demande():
	"""Modification d'une offre"""
	if check_connexion():
		sql_obj = sql.MysqlObject()
		mail = session['mail']
		id_od = request.form.get('id')
		horaires = request.form.get('horaires_data')

		if request.form.get('categorie') == "demande":
			# Demande
			demande = sql_obj.get_demande(id_od)
			# Vérification que l'auteur est celui qui demande la modification
			if mail == demande.auteur:
				sql_obj.modifier_demande(id_od, horaires)
			else:
				abort(403)
		else:
			# Offre
			offre = sql_obj.get_offre(id_od)
			# Vérification que l'auteur est celui qui demande la modification
			if mail == offre.auteur:
				sql_obj.modifier_offre(mail, id_od, horaires)
			else:
				abort(403)

		return redirect(url_for("profil_2", info_msg="Votre modification a bien été enregistrée."))
	else:
		return page_connexion()


# Suppression de la participation d'un utilisateur à une offre
@app.route('/quit')
def quit_tutorat():
	"""Sert à quitter un tutorat"""
	sql_obj = sql.MysqlObject()
	if check_connexion():
		if request.args.get('id'):
			offre_id = request.args.get('id')
			mail = session['mail']
			if sql_obj.delete_participant(offre_id, mail):
				return redirect(url_for("profil_2", info_msg="Votre retrait de ce Tutorat a bien été enregistré."))
			else:
				return redirect(url_for("profil_2", info_msg="Vous ne participez pas à ce Tutorat"))
		else:
			abort(403)
	else:
		# Redirection si l'utilisateur n'est pas connecté
		return page_connexion()


# Suppression de la participation d'un utilisateur à une offre
@app.route('/quit_2')
def quit_2():
	"""Sert à quitter une demande"""
	sql_obj = sql.MysqlObject()
	if check_connexion():
		if request.args.get('id'):
			demande_id = request.args.get('id')
			mail = session['mail']
			if sql_obj.quit_demande(demande_id, mail):
				return redirect(url_for("profil_2", info_msg="Votre retrait de ce Tutorat a bien été enregistré."))
			else:
				return redirect(url_for("profil_2", info_msg="Vous ne participez pas à ce Tutorat"))
		else:
			abort(403)
	else:
		# Redirection si l'utilisateur n'est pas connecté
		return page_connexion()

# Suppression d'un utilisateur
@app.route('/delete_user')
def delete_user():
	"""Supprime un utilisateur"""
	if check_connexion():
		mail = session['mail']
		if request.args.get('mail'):
			sql_obj = sql.MysqlObject()
			u_mail = request.args.get('mail')
			# Vérification que l'auteur ne se supprime pas lui-même
			if mail != u_mail:
				sql_obj.delete_account(u_mail)
				return redirect(request.referrer + "?info_msg=L'utilisateur a bien été supprimé.")
			else:
				abort(403)
		else:
			abort(403)
	else:
		return page_connexion()
	
	
# Suppression d'une offre
@app.route('/delete')
def delete():
	"""Supprime une offre"""
	if check_connexion():
		mail = session['mail']
		if request.args.get('id'):
			sql_obj = sql.MysqlObject()
			offre_id = request.args.get('id')
			offre = sql_obj.get_offre(offre_id)
			# Vérification que l'auteur est celui qui demande la suppression
			if mail == offre.auteur:
				sql_obj.delete_offer(offre_id)
				return redirect(url_for("profil", info_msg="Votre offre a bien été supprimée."))
			else:
				abort(403)
		else:
			abort(403)
	else:
		return page_connexion()


# Suppression d'une demande
@app.route('/delete3')
def delete3():
	"""Supprime une demande"""
	if check_connexion():
		mail = session['mail']
		if request.args.get('id'):
			sql_obj = sql.MysqlObject()
			demande_id = request.args.get('id')
			demande = sql_obj.get_demande(demande_id)
			# Vérification que l'auteur est celui qui demande la suppression
			if mail == demande.auteur:
				sql_obj.delete_demande(demande_id)
				return redirect(url_for("profil", info_msg="Votre demande a bien été supprimée."))
			else:
				abort(403)
		else:
			abort(403)
	else:
		return page_connexion()


# Suppression d'une offre (admin)
@app.route('/delete2')
def delete2():
	"""Supprime une offre (version admin)"""
	if check_connexion():
		admin_user = check_admin()
		if admin_user:
			if request.args.get('id'):
				offre_id = request.args.get('id')
				sql_obj = sql.MysqlObject()
				sql_obj.delete_offer(offre_id)
				return redirect(request.referrer + "?info_msg=La suppression a bien été effectuée.")
			else:
				abort(403)
		else:
			abort(403)
	else:
		return page_connexion()


# Suppression d'une demande (admin)
@app.route('/delete4')
def delete4():
	"""Supprime une demande (version admin)"""
	if check_connexion():
		admin_user = check_admin()
		if admin_user:
			if request.args.get('id'):
				demande_id = request.args.get('id')
				sql_obj = sql.MysqlObject()
				sql_obj.delete_demande(demande_id)
				return redirect(request.referrer + "?info_msg=La suppression a bien été effectuée.")
			else:
				abort(403)
		else:
			abort(403)
	else:
		return page_connexion()


# Validation d'une offre (admin)
@app.route('/validate')
def validate():
	"""Sert à valider une offre"""
	if check_connexion():
		admin_user = check_admin()
		if admin_user:
			if request.args.get('id'):
				disponible = 1
				offre_id = request.args.get('id')
				sql_obj = sql.MysqlObject()
				sql_obj.validate_offer(offre_id, disponible)
				return redirect(request.referrer + "?info_msg=L'offre a bien été validée.")
			else:
				abort(403)
		else:
			abort(403)
	else:
		return page_connexion()


# Validation d'une demande (admin)
@app.route('/validate2')
def validate2():
	"""Sert à valider une demande"""
	if check_connexion():
		admin_user = check_admin()
		if admin_user:
			if request.args.get('id'):
				disponible = 1
				demande_id = request.args.get('id')
				sql_obj = sql.MysqlObject()
				sql_obj.validate_demande(demande_id, disponible)
				return redirect(request.referrer + "?info_msg=La demande a bien été validée.")
			else:
				abort(403)
		else:
			abort(403)
	else:
		return page_connexion()


# Ban (admin)
@app.route('/ban')
def ban():
	"""Bannis un utilisateur"""
	if check_connexion():
		mail = session['mail']
		admin_user = check_admin()
		if admin_user:
			if request.args.get('mail'):
				mail_u = request.args.get('mail')
				if mail_u != mail:
					sql_obj = sql.MysqlObject()
					sql_obj.ban(mail_u)
					return redirect(url_for("admin_u",
											info_msg="Le statut de cet utilisateur a bien été mis à jour."))
				else:
					return render_template("error.html", message="Erreur - Vous ne pouvez pas vous bannir",
										   **locals())
			else:
				abort(403)
		else:
			abort(403)
	else:
		return page_connexion()


# Promouvoir (admin)
@app.route('/promote')
def promote():
	"""Promouvoir un utilisateur en administrateur"""
	if check_connexion():
		admin_user = check_admin()
		if admin_user:
			if request.args.get('mail'):
				mail = request.args.get('mail')
				sql_obj = sql.MysqlObject()
				sql_obj.promote(mail)
				return redirect(url_for("admin_u",
										info_msg="Le statut de cet utilisateur a bien été mis à jour."))
			else:
				abort(403)
		else:
			abort(403)
	else:
		return page_connexion()


# Retrograder (admin)
@app.route('/retrogr')
def retrogr():
	"""Rétrograder un administrateur en utilisateur"""
	if check_connexion():
		mail = session['mail']
		admin_user = check_admin()
		if admin_user:
			if request.args.get('mail'):
				mail_u = request.args.get('mail')
				if mail_u != mail:
					sql_obj = sql.MysqlObject()
					sql_obj.retrograder(mail_u)
					return redirect(url_for("admin_u",
											info_msg="Le statut de cet utilisateur a bien été mis à jour."))
				else:
					return render_template("error.html", message="Erreur - Vous ne pouvez pas vous rétrograder",
										   **locals())
			else:
				abort(403)
		else:
			abort(403)
	else:
		return page_connexion()


# Déconnexion
@app.route('/disconnect')
def deconnexion():
	"""Sert à se déconnecter du site"""
	if check_connexion():
		session.pop('mail', None)
		return redirect(url_for("connexion", info_msg='Vous avez bien été déconnecté.'))
	else:
		return redirect(url_for("connexion"))


# Remise à 0
@app.route('/reset')
def reset():
	"""Remet à 0 le site"""
	sql_obj = sql.MysqlObject()
	if check_connexion():
		admin_user = check_admin()
		if admin_user == 1:
			sql_obj.reset()
			return redirect(url_for('admin_ov', info_msg='Le site BlaBla-Tutorat a bien été remis à zéro.'))
		else:
			abort(403)
	else:
		return page_connexion()


# Gestion de l'erreur 404
@app.errorhandler(404)
def not_found(error):
	"""Affiche la page erreur 404"""
	return render_template("error.html", message="Erreur 404 - Ressource non trouvée", **locals())


# Gestion de l'erreur 403
@app.errorhandler(403)
def forbidden(error):
	"""Affiche la page erreur 403"""
	return render_template("error.html", message="Erreur 403 - Accès Interdit", **locals())


# Gestion de l'erreur 405
@app.errorhandler(405)
def method_not_allowed(error):
	"""Affiche la page erreur 405"""
	return render_template("error.html", message="Erreur 405 - Méthode de requête non autorisée", **locals())


def page_connexion():
	return redirect(url_for('connexion', info_msg="Veuillez vous connecter pour continuer."))


def page_recherche():
	return redirect(url_for("recherche"))


# Vérification connexion
def check_connexion():
	"""Vérifie si l'utilisateur est connecté"""
	# Verification mail non nul
	if 'mail' in session:
		sql_obj = sql.MysqlObject()
		mail = session['mail']
		# Vérification mail existe
		if sql_obj.mail_in_bdd(mail):
			if sql_obj.check_ban(mail):
				return False
			else:
				return True
		else:
			return False
	else:
		return False


# Vérification admin
def check_admin():
	"""Vérifie si l'utilisateur est admin"""
	if 'mail' in session:
		sql_obj = sql.MysqlObject()
		mail = session['mail']
		# Vérification mail existe
		if sql_obj.mail_in_bdd(mail):
			if sql_obj.get_user_info(mail).classe == "ADMIN":
				return True
			else:
				return False
		else:
			return False
	else:
		return False


def get_identites():
	return config.developp, config.webmaster


def get_infos_footer():
	return config.infos_etab, config.url_cgu


def get_creneau(n):
	return get_heure(n) + " - " + get_heure(n + 1)


def get_heure(n):
	h = str(8 + (n - 1) // 2) + "h"
	if (n - 1) % 2 == 1:
		m = "30"
	else:
		m = "00"
	return h + m

@app.route('/favicon.ico', methods=['GET', 'POST'])
def download():
	return send_from_directory(directory='', filename='favicon.ico')


# Possibilité d'appeler différentes fonctions depuis un template html
app.jinja_env.globals.update(check_connexion=check_connexion)
app.jinja_env.globals.update(get_identites=get_identites)
app.jinja_env.globals.update(get_infos_footer=get_infos_footer)
app.jinja_env.globals.update(get_crenau=get_creneau)
# Nécessaire pour faire fontionner les sessions
# (à garder secret pour que l'utilisateur ne puisse pas modifier les cookies)
app.secret_key = config.secret_key

# Lancement du serveur lors de l'exécution du fichier
if __name__ == '__main__':
	app.run()
