from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    send_file,
)
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta, timezone
from config import Config, resource_path, get_app_data_dir
import threading
import os
import sys

# Import PyQt5 for a 100% true standalone native desktop window
from PyQt5.QtCore import QUrl, QThread, Qt
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtGui import QIcon

app = Flask(
    __name__,
    template_folder=resource_path("templates"),
    static_folder=resource_path("static"),
)
app.config.from_object(Config)
db = SQLAlchemy(app)
# -----------------------------------------------------------
# TIMEZONE HELPER (Algeria local time = UTC+1)
# -----------------------------------------------------------
ALGERIA_TZ = timezone(timedelta(hours=1))


def now_local():
    return datetime.now(ALGERIA_TZ).replace(tzinfo=None)


# -----------------------------------------------------------
# DATABASE MODELS
# -----------------------------------------------------------
class Medicine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, unique=True)
    category = db.Column(db.String(100), nullable=True)
    buy_price = db.Column(db.Float, nullable=False)
    sell_price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    expiry_date = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=now_local)


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    parent_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=True)
    children = db.relationship(
        "Category",
        backref=db.backref("parent", remote_side="Category.id"),
        lazy="select",
        foreign_keys="Category.parent_id",
    )


class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    medicine_id = db.Column(db.Integer, db.ForeignKey("medicine.id"), nullable=True)
    medicine_name = db.Column(db.String(150), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    buy_price = db.Column(db.Float, nullable=False)
    sell_price = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    profit = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=now_local)


class Setting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    clinic_name = db.Column(
        db.String(200), default="Cabinet Vétérinaire Dr. Boulemaiz Azzeddine"
    )
    doctor_name = db.Column(db.String(150), default="Dr. Boulemaiz Azzeddine")
    currency = db.Column(db.String(20), default="DZD")
    default_lang = db.Column(db.String(10), default="fr")


# -----------------------------------------------------------
# TRANSLATION DICTIONARY (FR / AR / EN)
# -----------------------------------------------------------
TRANSLATIONS = {
    "fr": {
        "home": "Point de Vente",
        "stock": "Stock & Médicaments",
        "stock_entry": "Entrée en Stock",
        "reports": "Rapports & Bénéfices",
        "settings": "Paramètres",
        "net_profit_today": "Bénéfice Net Aujourd'hui",
        "net_profit_week": "Bénéfice Net Cette Semaine",
        "net_profit_month": "Bénéfice Net Ce Mois",
        "caisse": "Enregistrement des Ventes (Caisse)",
        "select_medicine": "Sélectionner un médicament",
        "quantity": "Quantité",
        "submit_sale": "Enregistrer la vente",
        "recent_sales": "Ventes Récentes",
        "medicine_name": "Nom du médicament",
        "unit_price": "Prix unitaire",
        "total": "Total",
        "profit": "Bénéfice",
        "date": "Date / Heure",
        "buy_price": "Prix d'achat",
        "sell_price": "Prix de vente",
        "current_qty": "Quantité en stock",
        "actions": "Actions",
        "add_medicine": "Ajouter un nouveau médicament",
        "edit_medicine": "Modifier",
        "save": "Enregistrer",
        "cancel": "Annuler",
        "batch_entry": "Enregistrement de nouveaux lots",
        "existing_or_new": "Choisir un médicament existant ou créer un nouveau",
        "add_quantity": "Quantité ajoutée",
        "confirm_entry": "Valider l'entrée",
        "reports_subtitle": "Analyse financière et historique des ventes",
        "currency": "DZD",
        "search_placeholder": "Rechercher un médicament...",
        "no_records": "Aucun enregistrement trouvé.",
        "developed_by": "Développé par Odil",
        "settings_title": "Configuration de la clinique",
        "doctor_name": "Nom du Médecin",
        "success_sale": "Vente enregistrée avec succès!",
        "insufficient_stock": "Stock insuffisant pour cet article!",
        "success_stock": "Stock mis à jour avec succès!",
        "btn_delete": "Supprimer",
        "confirm_delete_sale": "Annuler cette vente et remettre la quantité en stock ?",
        "receipt_title": "REÇU DE VENTE",
        "receipt_thanks": "Merci de votre confiance!",
        "btn_print_receipt": "Imprimer le reçu",
        "btn_close": "Fermer",
        "backup_title": "Sauvegarde des données",
        "backup_subtitle": "Protégez vos données en exportant une copie de sécurité.",
        "btn_backup": "💾 Télécharger une sauvegarde",
        "btn_restore": "📂 Restaurer une sauvegarde",
        "confirm_restore": "Restaurer remplacera les données actuelles. Continuer ?",
        "clear_sales_title": "Réinitialisation des statistiques",
        "clear_sales_sub": "Effacer tout l'historique des ventes pour remettre les bénéfices (aujourd'hui, cette semaine, ce mois) à zéro. Le stock de médicaments ne sera pas modifié.",
        "btn_clear_sales": "🗑️ Effacer l'historique des ventes",
        "confirm_clear_sales": "Êtes-vous sûr de vouloir supprimer DÉFINITIVEMENT tout l'historique des ventes et remettre les bénéfices à zéro ?",
        "confirm_delete_medicine": "Voulez-vous vraiment supprimer ce médicament DÉFINITIVEMENT du stock ? L'historique des ventes sera conservé.",
    },
    "ar": {
        "home": "نقطة البيع",
        "stock": "المخزون والأدوية",
        "stock_entry": "إدخال المخزون",
        "reports": "التقارير والأرباح",
        "settings": "الإعدادات",
        "net_profit_today": "صافي الربح اليوم",
        "net_profit_week": "صافي الربح هذا الأسبوع",
        "net_profit_month": "صافي الربح هذا الشهر",
        "caisse": "تسجيل المبيعات (نقطة البيع)",
        "select_medicine": "اختر الدواء",
        "quantity": "الكمية",
        "submit_sale": "تأكيد البيع",
        "recent_sales": "المبيعات الأخيرة",
        "medicine_name": "اسم الدواء",
        "unit_price": "سعر الوحدة",
        "total": "المجموع",
        "profit": "الربح",
        "date": "التاريخ / الوقت",
        "buy_price": "سعر الشراء",
        "sell_price": "سعر البيع",
        "current_qty": "الكمية الحالية",
        "actions": "إجراءات",
        "add_medicine": "إضافة دواء جديد",
        "edit_medicine": "تعديل",
        "save": "حفظ",
        "cancel": "إلغاء",
        "batch_entry": "تسجيل استلام دفعات جديدة",
        "existing_or_new": "اختر دواء موجود أو أدخل تفاصيل دواء جديد",
        "add_quantity": "الكمية المضافة",
        "confirm_entry": "تأكيد إدخال المخزون",
        "reports_subtitle": "التحليل المالي وسجل الأرباح",
        "currency": "د.ج",
        "search_placeholder": "ابحث عن دواء...",
        "no_records": "لا توجد بيانات مسجلة.",
        "developed_by": "تم التطوير بواسطة Odil",
        "settings_title": "إعدادات العيادة",
        "doctor_name": "اسم الطبيب",
        "success_sale": "تم تسجيل عملية البيع بنجاح!",
        "insufficient_stock": "الكمية في المخزون غير كافية!",
        "success_stock": "تم تحديث المخزون بنجاح!",
        "btn_delete": "حذف",
        "confirm_delete_sale": "هل تريد إلغاء عملية البيع هذه وإرجاع الكمية إلى المخزون؟",
        "receipt_title": "إيصال بيع",
        "receipt_thanks": "شكراً لثقتكم بنا!",
        "btn_print_receipt": "طباعة الإيصال",
        "btn_close": "إغلاق",
        "backup_title": "النسخ الاحتياطي للبيانات",
        "backup_subtitle": "احمِ بياناتك بتصدير نسخة أمان.",
        "btn_backup": "💾 تنزيل نسخة احتياطية",
        "btn_restore": "📂 استعادة نسخة احتياطية",
        "confirm_restore": "الاستعادة ستحلّ محل البيانات الحالية. هل تريد المتابعة؟",
        "clear_sales_title": "إعادة ضبط الإحصائيات والأرباح",
        "clear_sales_sub": "مسح سجل المبيعات بالكامل لإعادة الأرباح (اليوم، الأسبوع، الشهر) إلى الصفر. لن يتم تعديل مخزون الأدوية.",
        "btn_clear_sales": "🗑️ مسح سجل المبيعات بالكامل وتصفير الأرباح",
        "confirm_clear_sales": "هل أنت متأكد تماماً من رغبتك في حذف سجل المبيعات نهائياً وإعادة الأرباح إلى الصفر؟",
        "confirm_delete_medicine": "هل أنت متأكد تماماً من رغبتك في حذف هذا الدواء نهائياً من المخزون؟ سيتم الاحتفاظ بسجل مبيعاته السابقة.",
    },
    "en": {
        "home": "Point of Sale",
        "stock": "Stock & Inventory",
        "stock_entry": "Stock Entry",
        "reports": "Reports & Profits",
        "settings": "Settings",
        "net_profit_today": "Net Profit Today",
        "net_profit_week": "Net Profit This Week",
        "net_profit_month": "Net Profit This Month",
        "caisse": "Sales Recording (POS)",
        "select_medicine": "Select Medicine",
        "quantity": "Quantity",
        "submit_sale": "Record Sale",
        "recent_sales": "Recent Sales",
        "medicine_name": "Medicine Name",
        "unit_price": "Unit Price",
        "total": "Total",
        "profit": "Profit",
        "date": "Date / Time",
        "buy_price": "Buy Price",
        "sell_price": "Sell Price",
        "current_qty": "In Stock",
        "actions": "Actions",
        "add_medicine": "Add New Medicine",
        "edit_medicine": "Edit",
        "save": "Save",
        "cancel": "Cancel",
        "batch_entry": "Batch Inventory Arrival",
        "existing_or_new": "Select existing medicine or add new",
        "add_quantity": "Added Quantity",
        "confirm_entry": "Confirm Stock Entry",
        "reports_subtitle": "Financial Analysis & Sales History",
        "currency": "DZD",
        "search_placeholder": "Search medicine...",
        "no_records": "No records found.",
        "developed_by": "Developed by Odil",
        "settings_title": "Clinic Configuration",
        "doctor_name": "Doctor Name",
        "success_sale": "Sale recorded successfully!",
        "insufficient_stock": "Insufficient stock for this item!",
        "success_stock": "Stock updated successfully!",
        "btn_delete": "Delete",
        "confirm_delete_sale": "Cancel this sale and return the quantity to stock?",
        "receipt_title": "SALES RECEIPT",
        "receipt_thanks": "Thank you for your trust!",
        "btn_print_receipt": "Print Receipt",
        "btn_close": "Close",
        "backup_title": "Data Backup",
        "backup_subtitle": "Protect your data by exporting a safety copy.",
        "btn_backup": "💾 Download a backup",
        "btn_restore": "📂 Restore a backup",
        "confirm_restore": "Restoring will replace current data. Continue?",
        "clear_sales_title": "Reset Statistics",
        "clear_sales_sub": "Clear all sales history to reset profits (today, this week, this month) to zero. Medicine stock will not be affected.",
        "btn_clear_sales": "🗑️ Clear Sales History",
        "confirm_clear_sales": "Are you absolutely sure you want to PERMANENTLY delete all sales history and reset profits to zero?",
        "confirm_delete_medicine": "Are you sure you want to permanently delete this medicine from stock? Its sales history will be preserved.",
    },
}


# -----------------------------------------------------------
# CONTEXT PROCESSOR
# -----------------------------------------------------------
@app.context_processor
def inject_global_data():
    lang = session.get("lang", "fr")
    t = TRANSLATIONS.get(lang, TRANSLATIONS["fr"])
    now = now_local()
    today_start = datetime(now.year, now.month, now.day)
    week_start = today_start - timedelta(days=now.weekday())
    month_start = datetime(now.year, now.month, 1)
    all_sales = Sale.query.all()
    profit_today = sum(s.profit for s in all_sales if s.date >= today_start)
    profit_week = sum(s.profit for s in all_sales if s.date >= week_start)
    profit_month = sum(s.profit for s in all_sales if s.date >= month_start)
    settings = Setting.query.first()
    currency = settings.currency if settings else "DZD"
    clinic_name = (
        settings.clinic_name
        if settings
        else "Cabinet Vétérinaire Dr. Boulemaiz Azzeddine"
    )
    doctor_name = settings.doctor_name if settings else "Dr. Boulemaiz Azzeddine"
    return {
        "lang": lang,
        "t": t,
        "profit_today": f"{profit_today:,.2f} {currency}",
        "profit_week": f"{profit_week:,.2f} {currency}",
        "profit_month": f"{profit_month:,.2f} {currency}",
        "is_rtl": lang == "ar",
        "clinic_name": clinic_name,
        "doctor_name": doctor_name,
    }


# -----------------------------------------------------------
# ROUTES
# -----------------------------------------------------------
@app.route("/set_lang/<lang>")
def set_lang(lang):
    if lang in ["fr", "ar", "en"]:
        session["lang"] = lang
    return redirect(request.referrer or url_for("index"))


@app.route("/", methods=["GET", "POST"])
def index():
    lang = session.get("lang", "fr")
    t = TRANSLATIONS.get(lang, TRANSLATIONS["fr"])
    if request.method == "POST":
        medicine_id = request.form.get("medicine_id", type=int)
        quantity = request.form.get("quantity", type=int)
        if not medicine_id or not quantity or quantity <= 0:
            flash(
                "Quantité invalide."
                if lang == "fr"
                else ("كمية غير صحيحة." if lang == "ar" else "Invalid quantity."),
                "error",
            )
            return redirect(url_for("index"))
        med = Medicine.query.get(medicine_id)
        if not med:
            flash(
                "Médicament introuvable."
                if lang == "fr"
                else ("الدواء غير موجود." if lang == "ar" else "Medicine not found."),
                "error",
            )
            return redirect(url_for("index"))
        if med.quantity < quantity:
            flash(t["insufficient_stock"], "error")
            return redirect(url_for("index"))
        med.quantity -= quantity
        sale = Sale(
            medicine_id=med.id,
            medicine_name=med.name,
            quantity=quantity,
            buy_price=med.buy_price,
            sell_price=med.sell_price,
            total_price=med.sell_price * quantity,
            profit=(med.sell_price - med.buy_price) * quantity,
        )
        db.session.add(sale)
        db.session.commit()
        session["last_sale_id"] = sale.id
        flash(t["success_sale"], "success")
        return redirect(url_for("index"))
    medicines = (
        Medicine.query.filter(Medicine.quantity > 0).order_by(Medicine.name).all()
    )
    today_start = now_local().replace(hour=0, minute=0, second=0, microsecond=0)
    recent_sales = (
        Sale.query.filter(Sale.date >= today_start).order_by(Sale.date.desc()).all()
    )
    last_sale = None
    last_sale_id = session.pop("last_sale_id", None)
    if last_sale_id:
        last_sale = Sale.query.get(last_sale_id)
    return render_template(
        "index.html",
        medicines=medicines,
        recent_sales=recent_sales,
        last_sale=last_sale,
    )


@app.route("/delete_sale/<int:sale_id>", methods=["POST"])
def delete_sale(sale_id):
    lang = session.get("lang", "fr")
    sale = Sale.query.get(sale_id)
    if sale:
        med = Medicine.query.get(sale.medicine_id)
        if med:
            med.quantity += sale.quantity
        db.session.delete(sale)
        db.session.commit()
        flash(
            "Vente annulée, quantité remise en stock!"
            if lang == "fr"
            else (
                "تم إلغاء البيع وإرجاع الكمية إلى المخزون!"
                if lang == "ar"
                else "Sale cancelled, quantity returned to stock!"
            ),
            "success",
        )
    return redirect(url_for("index"))


@app.route("/stock", methods=["GET", "POST"])
def stock():
    lang = session.get("lang", "fr")
    t = TRANSLATIONS.get(lang, TRANSLATIONS["fr"])
    if request.method == "POST":
        med_id = request.form.get("med_id", type=int)
        name = request.form.get("name")
        category = request.form.get("category", "Général")
        buy_price = request.form.get("buy_price", type=float)
        sell_price = request.form.get("sell_price", type=float)
        quantity = request.form.get("quantity", type=int)
        if not name or buy_price is None or sell_price is None or quantity is None:
            flash(
                "Veuillez remplir tous les champs."
                if lang == "fr"
                else (
                    "يرجى ملء كافة الحقول."
                    if lang == "ar"
                    else "Please fill all fields."
                ),
                "error",
            )
            return redirect(url_for("stock"))
        if med_id:
            med = Medicine.query.get(med_id)
            if med:
                med.name, med.category, med.buy_price, med.sell_price, med.quantity = (
                    name,
                    category,
                    buy_price,
                    sell_price,
                    quantity,
                )
                db.session.commit()
                flash(t["success_stock"], "success")
        else:
            if Medicine.query.filter_by(name=name).first():
                flash(
                    "Ce médicament existe déjà."
                    if lang == "fr"
                    else (
                        "هذا الدواء مسجل مسبقاً."
                        if lang == "ar"
                        else "This medicine already exists."
                    ),
                    "error",
                )
            else:
                db.session.add(
                    Medicine(
                        name=name,
                        category=category,
                        buy_price=buy_price,
                        sell_price=sell_price,
                        quantity=quantity,
                    )
                )
                db.session.commit()
                flash(t["success_stock"], "success")
        return redirect(url_for("stock"))
    search = request.args.get("search", "")
    medicines = (
        Medicine.query.filter(Medicine.name.ilike(f"%{search}%"))
        .order_by(Medicine.name)
        .all()
        if search
        else Medicine.query.order_by(Medicine.name).all()
    )
    all_cats = Category.query.order_by(Category.name).all()
    return render_template(
        "stock.html", medicines=medicines, search=search, all_cats=all_cats
    )


@app.route("/delete_medicine/<int:med_id>", methods=["POST"])
def delete_medicine(med_id):
    """Delete a medicine from stock, keeping its sales history intact for reports."""
    lang = session.get("lang", "fr")
    med = Medicine.query.get(med_id)
    if med:
        try:
            Sale.query.filter_by(medicine_id=med_id).update({Sale.medicine_id: None})
            db.session.delete(med)
            db.session.commit()
            flash(
                "Médicament supprimé avec succès!"
                if lang == "fr"
                else (
                    "تم حذف الدواء بنجاح!"
                    if lang == "ar"
                    else "Medicine deleted successfully!"
                ),
                "success",
            )
        except Exception:
            flash(
                "Erreur lors de la suppression."
                if lang == "fr"
                else ("خطأ أثناء الحذف." if lang == "ar" else "Error during deletion."),
                "error",
            )
    return redirect(url_for("stock"))


@app.route("/stock_entry", methods=["GET", "POST"])
def stock_entry():
    lang = session.get("lang", "fr")
    t = TRANSLATIONS.get(lang, TRANSLATIONS["fr"])
    if request.method == "POST":
        med_id = request.form.get("medicine_id", type=int)
        new_name = request.form.get("new_name")
        buy_price = request.form.get("buy_price", type=float)
        sell_price = request.form.get("sell_price", type=float)
        add_quantity = request.form.get("add_quantity", type=int)
        if not add_quantity or add_quantity <= 0:
            flash(
                "Quantité invalide."
                if lang == "fr"
                else ("الكمية غير صحيحة." if lang == "ar" else "Invalid quantity."),
                "error",
            )
            return redirect(url_for("stock_entry"))
        if med_id:
            med = Medicine.query.get(med_id)
            if med:
                med.quantity += add_quantity
                if buy_price:
                    med.buy_price = buy_price
                if sell_price:
                    med.sell_price = sell_price
                db.session.commit()
                flash(t["success_stock"], "success")
        elif new_name and buy_price and sell_price:
            new_cat = request.form.get("new_category", "Général")
            existing = Medicine.query.filter_by(name=new_name).first()
            if existing:
                existing.quantity += add_quantity
                existing.buy_price, existing.sell_price = buy_price, sell_price
                if new_cat:
                    existing.category = new_cat
            else:
                db.session.add(
                    Medicine(
                        name=new_name,
                        category=new_cat,
                        buy_price=buy_price,
                        sell_price=sell_price,
                        quantity=add_quantity,
                    )
                )
            db.session.commit()
            flash(t["success_stock"], "success")
        else:
            flash(
                "Renseignez un médicament existant ou les détails d'un nouveau."
                if lang == "fr"
                else (
                    "يرجى اختيار دواء أو إدخال بيانات دواء جديد."
                    if lang == "ar"
                    else "Select an existing medicine or enter a new one."
                ),
                "error",
            )
        return redirect(url_for("stock_entry"))
    medicines = Medicine.query.order_by(Medicine.name).all()
    all_cats = Category.query.order_by(Category.name).all()
    parents = Category.query.filter_by(parent_id=None).order_by(Category.name).all()
    return render_template(
        "stock_entry.html", medicines=medicines, all_cats=all_cats, parents=parents
    )


@app.route("/categories", methods=["GET", "POST"])
def categories():
    lang = session.get("lang", "fr")
    if request.method == "POST":
        action = request.form.get("action")
        if action == "add":
            name = request.form.get("name", "").strip()
            parent_id = request.form.get("parent_id", type=int)
            if name and not Category.query.filter_by(name=name).first():
                db.session.add(Category(name=name, parent_id=parent_id or None))
                db.session.commit()
                flash(
                    "Catégorie ajoutée avec succès!"
                    if lang == "fr"
                    else (
                        "تمت إضافة الفئة بنجاح!"
                        if lang == "ar"
                        else "Category added successfully!"
                    ),
                    "success",
                )
            else:
                flash(
                    "Nom invalide ou déjà existant."
                    if lang == "fr"
                    else (
                        "الاسم غير صالح أو موجود مسبقاً."
                        if lang == "ar"
                        else "Invalid or duplicate name."
                    ),
                    "error",
                )
        elif action == "edit":
            cat_id = request.form.get("cat_id", type=int)
            name = request.form.get("name", "").strip()
            parent_id = request.form.get("parent_id", type=int)
            cat = Category.query.get(cat_id)
            if cat and name:
                cat.name = name
                cat.parent_id = parent_id or None
                db.session.commit()
                flash(
                    "Catégorie modifiée!"
                    if lang == "fr"
                    else ("تم تعديل الفئة!" if lang == "ar" else "Category updated!"),
                    "success",
                )
        elif action == "delete":
            cat_id = request.form.get("cat_id", type=int)
            cat = Category.query.get(cat_id)
            if cat:
                # Move children to parent
                for child in cat.children:
                    child.parent_id = cat.parent_id
                # Unlink medicines
                Medicine.query.filter_by(category=cat.name).update(
                    {"category": "Général"}
                )
                db.session.delete(cat)
                db.session.commit()
                flash(
                    "Catégorie supprimée!"
                    if lang == "fr"
                    else ("تم حذف الفئة!" if lang == "ar" else "Category deleted!"),
                    "success",
                )
        return redirect(url_for("categories"))
    parents = Category.query.filter_by(parent_id=None).order_by(Category.name).all()
    all_cats = Category.query.order_by(Category.name).all()
    return render_template("categories.html", parents=parents, all_cats=all_cats)


@app.route("/api/categories")
def api_categories():
    parents = Category.query.filter_by(parent_id=None).order_by(Category.name).all()
    result = []
    for p in parents:
        result.append({"id": p.id, "name": p.name, "parent_id": None})
        for c in p.children:
            result.append(
                {"id": c.id, "name": c.name, "parent_id": p.id, "parent_name": p.name}
            )
    return {"categories": result}


@app.route("/reports")
def reports():
    sales = Sale.query.order_by(Sale.date.desc()).all()
    reports_dict = {}
    for s in sales:
        d = s.date.strftime("%Y-%m-%d")
        if d not in reports_dict:
            reports_dict[d] = {"qty": 0, "total": 0.0, "profit": 0.0, "sales": []}
        reports_dict[d]["qty"] += s.quantity
        reports_dict[d]["total"] += s.total_price
        reports_dict[d]["profit"] += s.profit
        reports_dict[d]["sales"].append(s)
    return render_template("reports.html", reports=reports_dict)


@app.route("/settings", methods=["GET", "POST"])
def settings():
    lang = session.get("lang", "fr")
    setting = Setting.query.first()
    if request.method == "POST":
        clinic_name = request.form.get("clinic_name")
        doctor_name = request.form.get("doctor_name")
        currency = request.form.get("currency")
        default_lang = request.form.get("default_lang")
        if not setting:
            setting = Setting(
                clinic_name=clinic_name,
                doctor_name=doctor_name,
                currency=currency,
                default_lang=default_lang,
            )
            db.session.add(setting)
        else:
            if clinic_name:
                setting.clinic_name = clinic_name
            if doctor_name:
                setting.doctor_name = doctor_name
            if currency:
                setting.currency = currency
            if default_lang:
                setting.default_lang = default_lang
        db.session.commit()
        flash(
            "Paramètres enregistrés avec succès!"
            if lang == "fr"
            else (
                "تم حفظ الإعدادات بنجاح!"
                if lang == "ar"
                else "Settings saved successfully!"
            ),
            "success",
        )
        return redirect(url_for("settings"))
    return render_template("settings.html", setting=setting)


# -----------------------------------------------------------
# BACKUP & RESTORE & CLEAR SALES
# -----------------------------------------------------------
@app.route("/backup")
def backup():
    db_path = os.path.join(get_app_data_dir(), "database.db")
    if not os.path.exists(db_path):
        flash("Base de données introuvable.", "error")
        return redirect(url_for("settings"))
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return send_file(
        db_path, as_attachment=True, download_name=f"sauvegarde_{timestamp}.db"
    )


@app.route("/restore", methods=["POST"])
def restore():
    lang = session.get("lang", "fr")
    file = request.files.get("backup_file")
    db_path = os.path.join(get_app_data_dir(), "database.db")
    if not file or file.filename == "":
        flash(
            "Aucun fichier sélectionné."
            if lang == "fr"
            else ("لم يتم اختيار أي ملف." if lang == "ar" else "No file selected."),
            "error",
        )
        return redirect(url_for("settings"))
    try:
        file.save(db_path)
        flash(
            "Données restaurées avec succès!"
            if lang == "fr"
            else (
                "تمت استعادة البيانات بنجاح!"
                if lang == "ar"
                else "Data restored successfully!"
            ),
            "success",
        )
    except Exception:
        flash(
            "Erreur lors de la restauration."
            if lang == "fr"
            else ("خطأ أثناء الاستعادة." if lang == "ar" else "Error during restore."),
            "error",
        )
    return redirect(url_for("settings"))


@app.route("/clear_sales", methods=["POST"])
def clear_sales():
    lang = session.get("lang", "fr")
    try:
        db.session.query(Sale).delete()
        db.session.commit()
        flash(
            "Historique des ventes réinitialisé avec succès!"
            if lang == "fr"
            else (
                "تم مسح سجل المبيعات وتصفير الأرباح بنجاح!"
                if lang == "ar"
                else "Sales history reset successfully!"
            ),
            "success",
        )
    except Exception:
        flash(
            "Erreur lors de la réinitialisation."
            if lang == "fr"
            else ("خطأ أثناء إعادة الضبط." if lang == "ar" else "Error during reset."),
            "error",
        )
    return redirect(url_for("settings"))


# -----------------------------------------------------------
# INIT & SEED DATABASE
# -----------------------------------------------------------
def init_db():
    with app.app_context():
        db.create_all()
        if not Setting.query.first():
            db.session.add(
                Setting(
                    clinic_name="Cabinet Vétérinaire Dr. Boulemaiz Azzeddine",
                    doctor_name="Dr. Boulemaiz Azzeddine",
                    currency="DZD",
                    default_lang="fr",
                )
            )
            db.session.commit()
        # Seed categories if empty
        if not Category.query.first():
            CATS = [
                (
                    "Antibiotiques",
                    [
                        "Bêta-lactamines",
                        "Tétracyclines",
                        "Macrolides",
                        "Fluoroquinolones",
                        "Aminoglycosides",
                        "Sulfamidés",
                        "Phénicols",
                    ],
                ),
                (
                    "Antiparasitaires internes",
                    [
                        "Benzimidazoles",
                        "Avermectines",
                        "Tétrahydropyrimidines",
                        "Praziquantel",
                        "Associations polyvalentes",
                    ],
                ),
                (
                    "Antiparasitaires externes",
                    [
                        "Pyréthrinoïdes",
                        "Phénylpyrazoles",
                        "Organophosphorés",
                        "Isoxazolines",
                        "Acaricides",
                    ],
                ),
                (
                    "Anti-inflammatoires (AINS)",
                    [
                        "Oxicams",
                        "Acides propioniques",
                        "Acides fénamates",
                        "Salicylés",
                        "Coxibs",
                    ],
                ),
                (
                    "Corticostéroïdes",
                    ["Action courte", "Action longue (dépôt)", "Topiques"],
                ),
                (
                    "Anesthésiques et sédatifs",
                    [
                        "Anesthésiques dissociatifs",
                        "Alpha-2 agonistes",
                        "Anesthésiques IV",
                        "Anesthésiques locaux",
                        "Prémédications",
                        "Antagonistes",
                    ],
                ),
                ("Analgésiques", ["Opioïdes", "Non opioïdes"]),
                (
                    "Médicaments cardiovasculaires",
                    [
                        "Cardiotoniques",
                        "Diurétiques",
                        "Vasodilatateurs",
                        "Antiarythmiques",
                    ],
                ),
                (
                    "Médicaments respiratoires",
                    [
                        "Bronchodilatateurs",
                        "Mucolytiques",
                        "Analeptiques",
                        "Antitussifs",
                    ],
                ),
                (
                    "Médicaments digestifs",
                    [
                        "Antiémétiques",
                        "Antispasmodiques",
                        "Anti-diarrhéiques",
                        "Laxatifs",
                        "Anti-ulcéreux",
                        "Protecteurs gastriques",
                        "Stimulants appétit",
                    ],
                ),
                (
                    "Hormones et reproducteurs",
                    [
                        "Ocytociques",
                        "Progestagènes",
                        "Oestrogènes",
                        "Gonadotrophines",
                        "Prostaglandines",
                    ],
                ),
                (
                    "Dermatologiques",
                    [
                        "Antiseptiques cutanés",
                        "Cicatrisants",
                        "Antifongiques cutanés",
                        "Antibiotiques cutanés",
                        "Anti-inflammatoires cutanés",
                        "Émollients",
                        "Shampoings médicamenteux",
                    ],
                ),
                (
                    "Ophtalmologiques",
                    [
                        "Antibiotiques oculaires",
                        "Anti-inflammatoires oculaires",
                        "Associations oculaires",
                        "Antiglaucomateux",
                        "Lubrifiants oculaires",
                        "Mydriatiques",
                    ],
                ),
                (
                    "Otologiques",
                    [
                        "Antibiotiques auriculaires",
                        "Antifongiques auriculaires",
                        "Associations auriculaires",
                        "Nettoyants auriculaires",
                    ],
                ),
                ("Antifongiques systémiques", ["Azolés", "Polyènes"]),
                ("Antiviraux", ["Herpèsvirus", "Immunomodulateurs antiviraux"]),
                (
                    "Vitamines et minéraux",
                    [
                        "Vitamines liposolubles",
                        "Vitamines hydrosolubles",
                        "Minéraux et oligo-éléments",
                        "Complexes vitamino-minéraux",
                    ],
                ),
                (
                    "Compléments alimentaires",
                    [
                        "Probiotiques",
                        "Acides gras essentiels",
                        "Chondroprotecteurs",
                        "Hépatoprotecteurs",
                        "Compléments rénaux",
                    ],
                ),
                (
                    "Vaccins et immunologiques",
                    [
                        "Vaccins chiens",
                        "Vaccins chats",
                        "Vaccins bovins/ovins",
                        "Vaccins volailles",
                        "Sérums",
                        "Immunostimulants",
                    ],
                ),
                (
                    "Antiseptiques et désinfectants",
                    [
                        "Désinfectants cutanés",
                        "Désinfectants matériel",
                        "Désinfectants environnement",
                    ],
                ),
            ]
            for parent_name, children in CATS:
                parent = Category(name=parent_name)
                db.session.add(parent)
                db.session.flush()
                for child_name in children:
                    db.session.add(Category(name=child_name, parent_id=parent.id))
            db.session.commit()
        if not Medicine.query.first():
            meds = [
                Medicine(
                    name="Amoxicilline 500mg Vet",
                    category="Antibiotique",
                    buy_price=450,
                    sell_price=700,
                    quantity=45,
                ),
                Medicine(
                    name="Dectomax Injectable 50ml",
                    category="Antiparasitaire",
                    buy_price=3200,
                    sell_price=4500,
                    quantity=12,
                ),
                Medicine(
                    name="Vaccin Biocan DHPPi",
                    category="Vaccin",
                    buy_price=1200,
                    sell_price=2200,
                    quantity=25,
                ),
                Medicine(
                    name="Ivomec 1% 50ml",
                    category="Antiparasitaire",
                    buy_price=2500,
                    sell_price=3800,
                    quantity=18,
                ),
                Medicine(
                    name="Caniverm Comprimés (10 tab)",
                    category="Vermifuge",
                    buy_price=600,
                    sell_price=1100,
                    quantity=30,
                ),
                Medicine(
                    name="Alamycin LA 300 100ml",
                    category="Antibiotique",
                    buy_price=1800,
                    sell_price=2700,
                    quantity=15,
                ),
                Medicine(
                    name="Flamex Anti-inflammatoire",
                    category="AINS",
                    buy_price=900,
                    sell_price=1500,
                    quantity=20,
                ),
            ]
            db.session.bulk_save_objects(meds)
            db.session.commit()


# -----------------------------------------------------------
# 100% TRUE STANDALONE DESKTOP INTEGRATION (PyQt5 Chromium Window)
# -----------------------------------------------------------
class FlaskThread(QThread):
    def run(self):
        app.run(host=Config.HOST, port=Config.PORT, debug=False, use_reloader=False)


if __name__ == "__main__":
    init_db()
    # 1. Start Flask backend in a separate background thread
    flask_thread = FlaskThread()
    flask_thread.start()
    # 2. Create the native desktop application
    qt_app = QApplication(sys.argv)

    # Force sharp scaling on high-resolution screens (High-DPI)
    qt_app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    qt_app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    # Set custom window icon
    icon_path = resource_path("static/img/icon.ico")
    if os.path.exists(icon_path):
        qt_app.setWindowIcon(QIcon(icon_path))
    # Create the main window shell
    window = QMainWindow()
    window.setWindowTitle("Cabinet Vétérinaire - Dr. Boulemaiz Azzeddine")
    window.resize(1300, 850)
    window.setMinimumSize(1024, 768)
    # Embed the secure local web view (Chromium Engine)
    view = QWebEngineView()
    view.setUrl(QUrl(f"http://{Config.HOST}:{Config.PORT}/"))

    # Prevent browser right-click menu to make it a pure desktop application
    view.setContextMenuPolicy(Qt.NoContextMenu)
    window.setCentralWidget(view)
    window.show()
    # Stop Flask and exit safely when the window is closed
    sys.exit(qt_app.exec_())