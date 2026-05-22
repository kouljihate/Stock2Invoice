TRANSLATIONS = {
    'en': {},
    'ar': {},
    'fr': {},
}


def _get_translations(lang):
    base = TRANSLATIONS.get(lang, {})
    en = TRANSLATIONS.get('en', {})
    merged = en.copy()
    merged.update(base)
    return merged


def _(key, lang='en'):
    t = _get_translations(lang)
    return t.get(key, key)


# ─── Navigation ────────────────────────────────────────────
_en = TRANSLATIONS['en']
_ar = TRANSLATIONS['ar']
_fr = TRANSLATIONS['fr']

_ar['Dashboard'] = 'لوحة القيادة'
_fr['Dashboard'] = 'Tableau de bord'

_ar['Orders'] = 'الطلبات'
_fr['Orders'] = 'Commandes'

_ar['Products'] = 'المنتجات'
_fr['Products'] = 'Produits'

_ar['Invoices'] = 'الفواتير'
_fr['Invoices'] = 'Factures'

_ar['Admin'] = 'الإدارة'
_fr['Admin'] = 'Administration'

_ar['Users'] = 'المستخدمين'
_fr['Users'] = 'Utilisateurs'

_ar['Logout'] = 'تسجيل الخروج'
_fr['Logout'] = 'Déconnexion'

_ar['Language'] = 'اللغة'
_fr['Language'] = 'Langue'

_ar['Role'] = 'الدور'
_fr['Role'] = 'Rôle'

_ar['Company'] = 'الشركة'
_fr['Company'] = 'Société'

# ─── Sidebar ───────────────────────────────────────────────
# _ar['Procure-to-Pay'] = 'من الشراء إلى الدفع'
_ar['Procure-to-Pay'] = 'P2P'
# _fr['Procure-to-Pay'] = 'Approvisionnement à Paiement'
_fr['Procure-to-Pay'] = 'P2P'
_en['Procure-to-Pay'] = 'P2P'

# _ar['Quote-to-Cash'] = 'من العرض إلى التحصيل'
_ar['Quote-to-Cash'] = 'Q2C'
# _fr['Quote-to-Cash'] = 'Devis à Encaissement'
_fr['Quote-to-Cash'] = 'Q2C'
_en['Quote-to-Cash'] = 'Q2C'

_ar['Administration'] = 'الإدارة العامة'
_fr['Administration'] = 'Administration générale'

_ar['Suppliers'] = 'الموردين'
_fr['Suppliers'] = 'Fournisseurs'

_ar['Purchase Orders'] = 'أوامر الشراء'
_fr['Purchase Orders'] = 'Bons de commande'

_ar['Goods Receipt'] = 'استلام البضائع'
_fr['Goods Receipt'] = 'Réception des marchandises'

_ar['Supplier Invoices'] = 'فواتير الموردين'
_fr['Supplier Invoices'] = 'Factures fournisseurs'

_ar['Payments'] = 'المدفوعات'
_fr['Payments'] = 'Paiements'

_ar['Quotes'] = 'عروض الأسعار'
_fr['Quotes'] = 'Devis'

_ar['Customer Orders'] = 'طلبات العملاء'
_fr['Customer Orders'] = 'Commandes clients'

_ar['Delivery Notes'] = 'إشعارات التسليم'
_fr['Delivery Notes'] = 'Bons de livraison'

_ar['Customer Invoices'] = 'فواتير العملاء'
_fr['Customer Invoices'] = 'Factures clients'

_ar['Companies'] = 'الشركات'
_fr['Companies'] = 'Sociétés'

_ar['Products (Inventory)'] = 'المنتجات (المخزون)'
_fr['Produits (Inventaire)'] = 'Produits (Stock)'

# ─── Auth ──────────────────────────────────────────────────
_ar['Login'] = 'تسجيل الدخول'
_fr['Login'] = 'Connexion'

_ar['Register'] = 'التسجيل'
_fr['Register'] = 'Inscription'

_ar['Email'] = 'البريد الإلكتروني'
_fr['Email'] = 'E-mail'

_ar['Password'] = 'كلمة المرور'
_fr['Password'] = 'Mot de passe'

_ar['Name'] = 'الاسم'
_fr['Name'] = 'Nom'

_ar['Confirm Password'] = 'تأكيد كلمة المرور'
_fr['Confirm Password'] = 'Confirmer le mot de passe'

_ar['Remember Me'] = 'تذكرني'
_fr['Remember Me'] = 'Se souvenir de moi'

_ar['Forgot Password?'] = 'نسيت كلمة المرور؟'
_fr['Forgot Password?'] = 'Mot de passe oublié ?'

_ar["Don't have an account?"] = 'ليس لديك حساب؟'
_fr["Don't have an account?"] = "Vous n'avez pas de compte ?"

_ar['Already have an account?'] = 'لديك حساب بالفعل؟'
_fr['Already have an account?'] = 'Vous avez déjà un compte ?'

_ar['Sign In'] = 'تسجيل الدخول'
_fr['Sign In'] = 'Connexion'

_ar['Sign Up'] = 'إنشاء حساب'
_fr['Sign Up'] = "S'inscrire"

_ar['Session Expired'] = 'انتهت الجلسة'
_fr['Session Expired'] = 'Session expirée'

_ar['Your session has timed out. Please log in again to continue.'] = 'انتهت صلاحية جلستك. الرجاء تسجيل الدخول مرة أخرى للمتابعة.'
_fr['Your session has timed out. Please log in again to continue.'] = 'Votre session a expiré. Veuillez vous reconnecter pour continuer.'

_ar['Return to Login'] = 'العودة إلى تسجيل الدخول'
_fr['Return to Login'] = 'Retour à la connexion'

_ar['Welcome back'] = 'مرحباً بعودتك'
_fr['Welcome back'] = 'Bon retour'

# ─── Common Actions ────────────────────────────────────────
_ar['Add'] = 'إضافة'
_fr['Add'] = 'Ajouter'

_ar['Edit'] = 'تعديل'
_fr['Edit'] = 'Modifier'

_ar['Delete'] = 'حذف'
_fr['Delete'] = 'Supprimer'

_ar['View'] = 'عرض'
_fr['View'] = 'Voir'

_ar['Save'] = 'حفظ'
_fr['Save'] = 'Enregistrer'

_ar['Cancel'] = 'إلغاء'
_fr['Cancel'] = 'Annuler'

_ar['Create'] = 'إنشاء'
_fr['Create'] = 'Créer'

_ar['Update'] = 'تحديث'
_fr['Update'] = 'Mettre à jour'

_ar['Search'] = 'بحث'
_fr['Search'] = 'Rechercher'

_ar['Actions'] = 'الإجراءات'
_fr['Actions'] = 'Actions'

_ar['Back'] = 'رجوع'
_fr['Back'] = 'Retour'

_ar['Status'] = 'الحالة'
_fr['Status'] = 'Statut'

_ar['Date'] = 'التاريخ'
_fr['Date'] = 'Date'

_ar['Total'] = 'المجموع'
_fr['Total'] = 'Total'

_ar['Subtotal'] = 'المجموع الفرعي'
_fr['Subtotal'] = 'Sous-total'

_ar['Discount'] = 'الخصم'
_fr['Discount'] = 'Remise'

_ar['Tax'] = 'الضريبة'
_fr['Tax'] = 'Taxe'

_ar['Notes'] = 'ملاحظات'
_fr['Notes'] = 'Notes'

_ar['Description'] = 'الوصف'
_fr['Description'] = 'Description'

_ar['Quantity'] = 'الكمية'
_fr['Quantity'] = 'Quantité'

_ar['Unit Price'] = 'سعر الوحدة'
_fr['Unit Price'] = 'Prix unitaire'

_ar['Phone'] = 'الهاتف'
_fr['Phone'] = 'Téléphone'

_ar['Address'] = 'العنوان'
_fr['Address'] = 'Adresse'

_ar['City'] = 'المدينة'
_fr['City'] = 'Ville'

_ar['Contact'] = 'جهة الاتصال'
_fr['Contact'] = 'Contact'

_ar['No results found.'] = 'لا توجد نتائج.'
_fr['No results found.'] = 'Aucun résultat trouvé.'

_ar['No data yet.'] = 'لا توجد بيانات بعد.'
_fr['No data yet.'] = 'Pas encore de données.'

_ar['Are you sure?'] = 'هل أنت متأكد؟'
_fr['Are you sure?'] = 'Êtes-vous sûr ?'

_ar['Confirm'] = 'تأكيد'
_fr['Confirm'] = 'Confirmer'

_ar['Close'] = 'إغلاق'
_fr['Close'] = 'Fermer'

# ─── Statuses ──────────────────────────────────────────────
_ar['draft'] = 'مسودة'
_fr['draft'] = 'Brouillon'

_ar['pending'] = 'قيد الانتظار'
_fr['pending'] = 'En attente'

_ar['confirmed'] = 'مؤكد'
_fr['confirmed'] = 'Confirmé'

_ar['sent'] = 'مرسل'
_fr['sent'] = 'Envoyé'

_ar['paid'] = 'مدفوع'
_fr['paid'] = 'Payé'

_ar['cancelled'] = 'ملغي'
_fr['cancelled'] = 'Annulé'

_ar['delivered'] = 'تم التسليم'
_fr['delivered'] = 'Livré'

_ar['shipped'] = 'تم الشحن'
_fr['shipped'] = 'Expédié'

_ar['received'] = 'مستلم'
_fr['received'] = 'Reçu'

_ar['approved'] = 'معتمد'
_fr['approved'] = 'Approuvé'

_ar['cleared'] = 'مقاصة'
_fr['cleared'] = 'Compensé'

_ar['accepted'] = 'مقبول'
_fr['accepted'] = 'Accepté'

# ─── Module specific ──────────────────────────────────────
_ar['Supplier'] = 'المورد'
_fr['Supplier'] = 'Fournisseur'

_ar['Customer'] = 'العميل'
_fr['Customer'] = 'Client'

_ar['PO #'] = 'رقم أمر الشراء'
_fr['PO #'] = 'N° BC'

_ar['Invoice #'] = 'رقم الفاتورة'
_fr['Invoice #'] = 'N° Facture'

_ar['Quote #'] = 'رقم عرض السعر'
_fr['Quote #'] = 'N° Devis'

_ar['Order #'] = 'رقم الطلب'
_fr['Order #'] = 'N° Commande'

_ar['Payment #'] = 'رقم الدفع'
_fr['Payment #'] = 'N° Paiement'

_ar['Receipt #'] = 'رقم الاستلام'
_fr['Receipt #'] = 'N° Réception'

_ar['DN #'] = 'رقم إشعار التسليم'
_fr['DN #'] = 'N° BL'

_ar['Due Date'] = 'تاريخ الاستحقاق'
_fr['Due Date'] = 'Date d\'échéance'

_ar['Valid Until'] = 'صالح حتى'
_fr['Valid Until'] = 'Valable jusqu\'au'

_ar['Payment Method'] = 'طريقة الدفع'
_fr['Payment Method'] = 'Méthode de paiement'

_ar['Reference'] = 'المرجع'
_fr['Reference'] = 'Référence'

_ar['Amount'] = 'المبلغ'
_fr['Amount'] = 'Montant'

_ar['Item Name'] = 'اسم الصنف'
_fr['Item Name'] = 'Nom de l\'article'

_ar['SKU'] = 'رمز الصنف'
_fr['SKU'] = 'Code article'

_ar['Line Items'] = 'بنود الفاتورة'
_fr['Line Items'] = 'Lignes d\'articles'

_ar['Add Item'] = 'إضافة بند'
_fr['Add Item'] = 'Ajouter une ligne'

_ar['Customer Name'] = 'اسم العميل'
_fr['Customer Name'] = 'Nom du client'

_ar['Customer Email'] = 'البريد الإلكتروني للعميل'
_fr['Customer Email'] = 'E-mail du client'

_ar['Customer Address'] = 'عنوان العميل'
_fr['Customer Address'] = 'Adresse du client'

_ar['Supplier Name'] = 'اسم المورد'
_fr['Supplier Name'] = 'Nom du fournisseur'

_ar['Contact Name'] = 'اسم جهة الاتصال'
_fr['Contact Name'] = 'Nom du contact'

_ar['Payment Terms'] = 'شروط الدفع'
_fr['Payment Terms'] = 'Conditions de paiement'

_ar['ICE'] = 'رقم التعريف الضريبي'
_fr['ICE'] = 'ICE'

_ar['RC'] = 'السجل التجاري'
_fr['RC'] = 'RC'

_ar['Logo'] = 'الشعار'
_fr['Logo'] = 'Logo'

_ar['Upload'] = 'رفع'
_fr['Upload'] = 'Télécharger'

# ─── Stock ─────────────────────────────────────────────────
_ar['Product Name'] = 'اسم المنتج'
_fr['Product Name'] = 'Nom du produit'

_ar['Category'] = 'الفئة'
_fr['Category'] = 'Catégorie'

_ar['Low Stock Threshold'] = 'حد المخزون المنخفض'
_fr['Low Stock Threshold'] = 'Seuil de stock bas'

_ar['Tax Rate'] = 'نسبة الضريبة'
_fr['Tax Rate'] = 'Taux de taxe'

_ar['In Stock'] = 'في المخزون'
_fr['In Stock'] = 'En stock'

_ar['Out of Stock'] = 'غير متوفر'
_fr['Out of Stock'] = 'En rupture'

_ar['Bulk Upload'] = 'رفع جماعي'
_fr['Bulk Upload'] = 'Import en masse'

# ─── Time ──────────────────────────────────────────────────
_ar['Today'] = 'اليوم'
_fr['Today'] = "Aujourd'hui"

_ar['This Week'] = 'هذا الأسبوع'
_fr['This Week'] = 'Cette semaine'

_ar['This Month'] = 'هذا الشهر'
_fr['This Month'] = 'Ce mois-ci'

_ar['Recent'] = 'الأخيرة'
_fr['Recent'] = 'Récent'

_ar['See All'] = 'عرض الكل'
_fr['See All'] = 'Voir tout'

# ─── Errors ────────────────────────────────────────────────
_ar['Error'] = 'خطأ'
_fr['Error'] = 'Erreur'

_ar['Success'] = 'نجاح'
_fr['Success'] = 'Succès'

_ar['Warning'] = 'تحذير'
_fr['Warning'] = 'Avertissement'

_ar['Info'] = 'معلومات'
_fr['Info'] = 'Information'

_ar['Page not found'] = 'الصفحة غير موجودة'
_fr['Page not found'] = 'Page non trouvée'

_ar['Forbidden'] = 'ممنوع'
_fr['Forbidden'] = 'Interdit'

_ar['Internal server error'] = 'خطأ داخلي في الخادم'
_fr['Internal server error'] = 'Erreur interne du serveur'

_ar['Unauthorized'] = 'غير مصرح'
_fr['Unauthorized'] = 'Non autorisé'

_ar['Bad request'] = 'طلب غير صالح'
_fr['Bad request'] = 'Requête invalide'

_ar['Go Home'] = 'الذهاب إلى الرئيسية'
_fr['Go Home'] = 'Aller à l\'accueil'

_ar['An unexpected error occurred. Please try again later.'] = 'حدث خطأ غير متوقع. الرجاء المحاولة مرة أخرى لاحقًا.'
_fr['An unexpected error occurred. Please try again later.'] = 'Une erreur inattendue s\'est produite. Veuillez réessayer plus tard.'

_ar['You do not have permission to access this page.'] = 'ليس لديك إذن للوصول إلى هذه الصفحة.'
_fr['You do not have permission to access this page.'] = 'Vous n\'avez pas la permission d\'accéder à cette page.'

_ar['Recent Stock Movements'] = 'حركات المخزون الأخيرة'
_fr['Recent Stock Movements'] = 'Mouvements de stock récents'

_ar['No recent stock movements.'] = 'لا توجد حركات مخزون حديثة.'
_fr['No recent stock movements.'] = 'Aucun mouvement de stock récent.'

_ar['Low Stock Alerts'] = 'تنبيهات المخزون المنخفض'
_fr['Low Stock Alerts'] = 'Alertes de stock bas'

_ar['No low stock alerts.'] = 'لا توجد تنبيهات مخزون منخفض.'
_fr['No low stock alerts.'] = 'Aucune alerte de stock bas.'

_ar['Recent Invoices'] = 'الفواتير الأخيرة'
_fr['Recent Invoices'] = 'Factures récentes'

_ar['No recent invoices.'] = 'لا توجد فواتير حديثة.'
_fr['No recent invoices.'] = 'Aucune facture récente.'

_ar['Recent Orders'] = 'الطلبات الأخيرة'
_fr['Recent Orders'] = 'Commandes récentes'

_ar['No recent orders.'] = 'لا توجد طلبات حديثة.'
_fr['No recent orders.'] = 'Aucune commande récente.'

_ar['Total Products'] = 'إجمالي المنتجات'
_fr['Total Products'] = 'Total des produits'

_ar['Stock Value'] = 'قيمة المخزون'
_fr['Stock Value'] = 'Valeur du stock'

_ar['Low Stock Products'] = 'المنتجات ذات المخزون المنخفض'
_fr['Low Stock Products'] = 'Produits en stock bas'

_ar['Low Stock Items'] = 'عناصر المخزون المنخفض'
_fr['Low Stock Items'] = 'Articles en stock bas'

_ar['Open Invoices'] = 'الفواتير المفتوحة'
_fr['Open Invoices'] = 'Factures ouvertes'

_ar['Welcome'] = 'مرحباً'
_fr['Welcome'] = 'Bienvenue'

_ar['product(s)'] = 'منتج(ات)'
_fr['product(s)'] = 'produit(s)'

_ar['are below their low-stock threshold.'] = 'أقل من حد المخزون المنخفض.'
_fr['are below their low-stock threshold.'] = 'sont en dessous du seuil de stock bas.'

_ar['New'] = 'جديد'
_fr['New'] = 'Nouveau'

_ar['No invoices yet.'] = 'لا توجد فواتير بعد.'
_fr['No invoices yet.'] = 'Aucune facture pour l\'instant.'

_ar['No movements yet.'] = 'لا توجد حركات بعد.'
_fr['No movements yet.'] = 'Aucun mouvement pour l\'instant.'

_ar['Stock by Category'] = 'المخزون حسب الفئة'
_fr['Stock by Category'] = 'Stock par catégorie'

_ar['Total Qty'] = 'إجمالي الكمية'
_fr['Total Qty'] = 'Qté totale'

_ar['Value'] = 'القيمة'
_fr['Value'] = 'Valeur'

_ar['Uncategorized'] = 'بدون تصنيف'
_fr['Uncategorized'] = 'Non catégorisé'

# ─── New Keys from Templates ──────────────────────────────
_ar['Add Product'] = 'إضافة منتج'
_fr['Add Product'] = 'Ajouter un produit'

_ar['Add Bulk Products'] = 'إضافة منتجات بالجملة'
_fr['Add Bulk Products'] = 'Ajouter des produits en vrac'

_ar['Search by name or SKU...'] = 'البحث بالاسم أو SKU...'
_fr['Search by name or SKU...'] = 'Rechercher par nom ou SKU...'

_ar['Filter by category...'] = 'تصفية حسب الفئة...'
_fr['Filter by category...'] = 'Filtrer par catégorie...'

_ar['Qty'] = 'الكمية'
_fr['Qty'] = 'Qté'

_ar['Price'] = 'السعر'
_fr['Price'] = 'Prix'

_ar['Low'] = 'منخفض'
_fr['Low'] = 'Bas'

_ar['No products found.'] = 'لم يتم العثور على منتجات.'
_fr['No products found.'] = 'Aucun produit trouvé.'

_ar['Product'] = 'المنتج'
_fr['Product'] = 'Produit'

_ar['Details'] = 'التفاصيل'
_fr['Details'] = 'Détails'

_ar['Total Value'] = 'القيمة الإجمالية'
_fr['Total Value'] = 'Valeur totale'

_ar['Stock Movements'] = 'حركات المخزون'
_fr['Stock Movements'] = 'Mouvements de stock'

_ar['Type'] = 'النوع'
_fr['Type'] = 'Type'

_ar['Reason'] = 'السبب'
_fr['Reason'] = 'Motif'

_ar['Before'] = 'قبل'
_fr['Before'] = 'Avant'

_ar['After'] = 'بعد'
_fr['After'] = 'Après'

_ar['No movements recorded.'] = 'لا توجد حركات مسجلة.'
_fr['No movements recorded.'] = 'Aucun mouvement enregistré.'

_ar['in'] = 'داخل'
_fr['in'] = 'entrée'

_ar['out'] = 'خارج'
_fr['out'] = 'sortie'

_ar['Import Results'] = 'نتائج الاستيراد'
_fr['Import Results'] = 'Résultats d\'importation'

_ar['Imported'] = 'تم الاستيراد'
_fr['Imported'] = 'Importé'

_ar['OK'] = 'موافق'
_fr['OK'] = 'OK'

_ar['Upload Another File'] = 'رفع ملف آخر'
_fr['Upload Another File'] = 'Télécharger un autre fichier'

_ar['Preview'] = 'معاينة'
_fr['Preview'] = 'Aperçu'

_ar['loaded'] = 'تم التحميل'
_fr['loaded'] = 'chargé(s)'

_ar['Upload File'] = 'رفع ملف'
_fr['Upload File'] = 'Télécharger un fichier'

_ar['File Format'] = 'تنسيق الملف'
_fr['File Format'] = 'Format du fichier'

_ar['CSV'] = 'CSV'
_fr['CSV'] = 'CSV'

_ar['JSON'] = 'JSON'
_fr['JSON'] = 'JSON'

_ar['Select JSON or CSV file'] = 'اختر ملف JSON أو CSV'
_fr['Select JSON or CSV file'] = 'Sélectionner un fichier JSON ou CSV'

_ar['Load File'] = 'تحميل الملف'
_fr['Load File'] = 'Charger le fichier'

_ar['Validate & Save All'] = 'التحقق وحفظ الكل'
_fr['Validate & Save All'] = 'Valider et tout enregistrer'

_ar['Back to Products'] = 'العودة إلى المنتجات'
_fr['Back to Products'] = 'Retour aux produits'

_ar['Include headers row:'] = 'تضمين صف العناوين:'
_fr['Include headers row:'] = 'Inclure la ligne d\'en-têtes :'

_ar['Array of objects:'] = 'مصفوفة من الكائنات:'
_fr['Array of objects:'] = 'Tableau d\'objets :'

_ar['Only name and sku are required.'] = 'الاسم و SKU فقط مطلوبان.'
_fr['Only name and sku are required.'] = 'Seuls le nom et le SKU sont requis.'

_ar['Threshold'] = 'الحد'
_fr['Threshold'] = 'Seuil'

_ar['New Order'] = 'طلب جديد'
_fr['New Order'] = 'Nouvelle commande'

_ar['All Statuses'] = 'جميع الحالات'
_fr['All Statuses'] = 'Tous les statuts'

_ar['Pending'] = 'قيد الانتظار'
_fr['Pending'] = 'En attente'

_ar['Confirmed'] = 'مؤكد'
_fr['Confirmed'] = 'Confirmé'

_ar['Shipped'] = 'تم الشحن'
_fr['Shipped'] = 'Expédié'

_ar['Delivered'] = 'تم التسليم'
_fr['Delivered'] = 'Livré'

_ar['Cancelled'] = 'ملغي'
_fr['Cancelled'] = 'Annulé'

_ar['No orders found.'] = 'لم يتم العثور على طلبات.'
_fr['No orders found.'] = 'Aucune commande trouvée.'

_ar['Order'] = 'الطلب'
_fr['Order'] = 'Commande'

_ar['Order Details'] = 'تفاصيل الطلب'
_fr['Order Details'] = 'Détails de la commande'

_ar['Order Date'] = 'تاريخ الطلب'
_fr['Order Date'] = 'Date de commande'

_ar['Invoice generated:'] = 'تم إنشاء الفاتورة:'
_fr['Invoice generated:'] = 'Facture générée :'

_ar['Item'] = 'الصنف'
_fr['Item'] = 'Article'

_ar['Notes:'] = 'ملاحظات:'
_fr['Notes:'] = 'Notes :'

_ar['Change Status'] = 'تغيير الحالة'
_fr['Change Status'] = 'Changer le statut'

_ar['Update Status'] = 'تحديث الحالة'
_fr['Update Status'] = 'Mettre à jour le statut'

_ar['View Invoice'] = 'عرض الفاتورة'
_fr['View Invoice'] = 'Voir la facture'

_ar['Create Order'] = 'إنشاء الطلب'
_fr['Create Order'] = 'Créer la commande'

_ar['-- Select Product --'] = '-- اختر المنتج --'
_fr['-- Select Product --'] = '-- Sélectionner un produit --'

_ar['in stock'] = 'متوفر'
_fr['in stock'] = 'en stock'

_ar['New Invoice'] = 'فاتورة جديدة'
_fr['New Invoice'] = 'Nouvelle facture'

_ar['Draft'] = 'مسودة'
_fr['Draft'] = 'Brouillon'

_ar['Sent'] = 'مرسل'
_fr['Sent'] = 'Envoyé'

_ar['Paid'] = 'مدفوع'
_fr['Paid'] = 'Payé'

_ar['No invoices found.'] = 'لم يتم العثور على فواتير.'
_fr['No invoices found.'] = 'Aucune facture trouvée.'

_ar['Invoice'] = 'الفاتورة'
_fr['Invoice'] = 'Facture'

_ar['Invoice Details'] = 'تفاصيل الفاتورة'
_fr['Invoice Details'] = 'Détails de la facture'

_ar['Invoice Date'] = 'تاريخ الفاتورة'
_fr['Invoice Date'] = 'Date de facture'

_ar['Print'] = 'طباعة'
_fr['Print'] = 'Imprimer'

_ar['Print / PDF'] = 'طباعة / PDF'
_fr['Print / PDF'] = 'Imprimer / PDF'

_ar['Create Invoice'] = 'إنشاء الفاتورة'
_fr['Create Invoice'] = 'Créer la facture'

_ar['INVOICE'] = 'فاتورة'
_fr['INVOICE'] = 'FACTURE'

_ar['Date:'] = 'التاريخ:'
_fr['Date:'] = 'Date :'

_ar['Bill To:'] = 'الفاتورة إلى:'
_fr['Bill To:'] = 'Facturer à :'

_ar['Thank you for your business!'] = 'شكراً لتعاملكم معنا!'
_fr['Thank you for your business!'] = 'Merci pour votre confiance !'

_ar['Add Supplier'] = 'إضافة مورد'
_fr['Add Supplier'] = 'Ajouter un fournisseur'

_ar['No suppliers yet.'] = 'لا يوجد موردون بعد.'
_fr['No suppliers yet.'] = 'Aucun fournisseur pour l\'instant.'

_ar['Add Bulk Suppliers'] = 'إضافة موردين بالجملة'
_fr['Add Bulk Suppliers'] = 'Ajouter des fournisseurs en masse'

_ar['supplier(s)'] = 'مورد(ون)'
_fr['supplier(s)'] = 'fournisseur(s)'

_ar['Back to Suppliers'] = 'العودة إلى الموردين'
_fr['Back to Suppliers'] = 'Retour aux fournisseurs'

_ar['Only name is required.'] = 'الاسم فقط مطلوب.'
_fr['Only name is required.'] = 'Seul le nom est requis.'

_ar['Headers:'] = 'العناوين:'
_fr['Headers:'] = 'En-têtes :'

_ar['Customers'] = 'العملاء'
_fr['Customers'] = 'Clients'

_ar['Add Customer'] = 'إضافة عميل'
_fr['Add Customer'] = 'Ajouter un client'

_ar['Add Bulk Customers'] = 'إضافة عملاء بالجملة'
_fr['Add Bulk Customers'] = 'Ajouter des clients en masse'

_ar['No customers yet.'] = 'لا يوجد عملاء بعد.'
_fr['No customers yet.'] = 'Aucun client pour l\'instant.'

_ar['Back to Customers'] = 'العودة إلى العملاء'
_fr['Back to Customers'] = 'Retour aux clients'

_ar['Create Customer'] = 'إنشاء العميل'
_fr['Create Customer'] = 'Créer le client'

_ar['Edit Customer'] = 'تعديل العميل'
_fr['Edit Customer'] = 'Modifier le client'

_ar['Customer'] = 'العميل'
_fr['Customer'] = 'Client'

_ar['customer(s)'] = 'عميل(اء)'
_fr['customer(s)'] = 'client(s)'

_ar['Edit Quote'] = 'تعديل عرض السعر'
_fr['Edit Quote'] = 'Modifier le devis'
_ar['Delete Quote'] = 'حذف عرض السعر'
_fr['Delete Quote'] = 'Supprimer le devis'
_ar['Send to Customer'] = 'إرسال إلى العميل'
_fr['Send to Customer'] = 'Envoyer au client'
_ar['Quote sent.'] = 'تم إرسال عرض السعر.'
_fr['Quote sent.'] = 'Devis envoyé.'
_ar['Quote deleted.'] = 'تم حذف عرض السعر.'
_fr['Quote deleted.'] = 'Devis supprimé.'
_ar['Quote updated.'] = 'تم تحديث عرض السعر.'
_fr['Quote updated.'] = 'Devis mis à jour.'
_ar['Accepted'] = 'مقبول'
_fr['Accepted'] = 'Accepté'

_ar['Private'] = 'فرد'
_fr['Private'] = 'Privé'

_ar['Share'] = 'مشاركة'
_fr['Share'] = 'Partager'
_ar['Download PDF'] = 'تحميل PDF'
_fr['Download PDF'] = 'Télécharger PDF'
_ar['ORDER'] = 'الطلب'
_fr['ORDER'] = 'COMMANDE'
_ar['Generated on'] = 'تم الإنشاء في'
_fr['Generated on'] = 'Généré le'

_ar['Validate Quote'] = 'التحقق من عرض السعر'
_fr['Validate Quote'] = 'Valider le devis'
_ar['Quote converted to order:'] = 'تم تحويل عرض السعر إلى طلب:'
_fr['Quote converted to order:'] = 'Devis converti en commande :'

_ar['e.g. Net 30'] = 'مثل: صافي 30'
_fr['e.g. Net 30'] = 'ex. Net 30'

_ar['Add PO'] = 'إضافة أمر شراء'
_fr['Add PO'] = 'Ajouter BC'

_ar['No purchase orders yet.'] = 'لا توجد أوامر شراء بعد.'
_fr['No purchase orders yet.'] = 'Aucun bon de commande pour l\'instant.'

_ar['Purchase Order'] = 'أمر الشراء'
_fr['Purchase Order'] = 'Bon de commande'

_ar['Created'] = 'تم الإنشاء'
_fr['Created'] = 'Créé le'

_ar['New Purchase Order'] = 'أمر شراء جديد'
_fr['New Purchase Order'] = 'Nouveau bon de commande'

_ar['-- Select Supplier --'] = '-- اختر المورد --'
_fr['-- Select Supplier --'] = '-- Sélectionner un fournisseur --'

_ar['Item name'] = 'اسم الصنف'
_fr['Item name'] = 'Nom de l\'article'

_ar['Create Purchase Order'] = 'إنشاء أمر الشراء'
_fr['Create Purchase Order'] = 'Créer le bon de commande'

_ar['Goods Receipts'] = 'استلام البضائع'
_fr['Goods Receipts'] = 'Réceptions de marchandises'

_ar['Add Receipt'] = 'إضافة استلام'
_fr['Add Receipt'] = 'Ajouter une réception'

_ar['No goods receipts yet.'] = 'لا توجد استلامات بضائع بعد.'
_fr['No goods receipts yet.'] = 'Aucune réception pour l\'instant.'

_ar['New Goods Receipt'] = 'استلام بضائع جديد'
_fr['New Goods Receipt'] = 'Nouvelle réception de marchandises'

_ar['-- Select PO --'] = '-- اختر أمر الشراء --'
_fr['-- Select PO --'] = '-- Sélectionner un BC --'

_ar['Received Items'] = 'المواد المستلمة'
_fr['Received Items'] = 'Articles reçus'

_ar['Create Goods Receipt'] = 'إنشاء استلام البضائع'
_fr['Create Goods Receipt'] = 'Créer la réception'

_ar['Add Invoice'] = 'إضافة فاتورة'
_fr['Add Invoice'] = 'Ajouter une facture'

_ar['No supplier invoices yet.'] = 'لا توجد فواتير موردين بعد.'
_fr['No supplier invoices yet.'] = 'Aucune facture fournisseur pour l\'instant.'

_ar['New Supplier Invoice'] = 'فاتورة مورد جديدة'
_fr['New Supplier Invoice'] = 'Nouvelle facture fournisseur'

_ar['PO Reference'] = 'مرجع أمر الشراء'
_fr['PO Reference'] = 'Référence BC'

_ar['PO number'] = 'رقم أمر الشراء'
_fr['PO number'] = 'Numéro BC'

_ar['Add Payment'] = 'إضافة دفعة'
_fr['Add Payment'] = 'Ajouter un paiement'

_ar['Method'] = 'الطريقة'
_fr['Method'] = 'Méthode'

_ar['No payments yet.'] = 'لا توجد مدفوعات بعد.'
_fr['No payments yet.'] = 'Aucun paiement pour l\'instant.'

_ar['New Payment'] = 'دفعة جديدة'
_fr['New Payment'] = 'Nouveau paiement'

_ar['Invoice Reference'] = 'مرجع الفاتورة'
_fr['Invoice Reference'] = 'Référence facture'

_ar['Invoice number'] = 'رقم الفاتورة'
_fr['Invoice number'] = 'Numéro de facture'

_ar['Payment Date'] = 'تاريخ الدفع'
_fr['Payment Date'] = 'Date de paiement'

_ar['-- Select --'] = '-- اختر --'
_fr['-- Select --'] = '-- Sélectionner --'

_ar['Bank Transfer'] = 'تحويل بنكي'
_fr['Bank Transfer'] = 'Virement bancaire'

_ar['Check'] = 'شيك'
_fr['Check'] = 'Chèque'

_ar['Cash'] = 'نقداً'
_fr['Cash'] = 'Espèces'

_ar['Credit Card'] = 'بطاقة ائتمان'
_fr['Credit Card'] = 'Carte de crédit'

_ar['Check # or ref'] = 'رقم الشيك أو المرجع'
_fr['Check # or ref'] = 'N° chèque ou réf'

_ar['Create Payment'] = 'إنشاء الدفعة'
_fr['Create Payment'] = 'Créer le paiement'

_ar['Customer Quotes'] = 'عروض الأسعار'
_fr['Customer Quotes'] = 'Devis clients'

_ar['Add Quote'] = 'إضافة عرض سعر'
_fr['Add Quote'] = 'Ajouter un devis'

_ar['No quotes yet.'] = 'لا توجد عروض أسعار بعد.'
_fr['No quotes yet.'] = 'Aucun devis pour l\'instant.'

_ar['Quote'] = 'عرض السعر'
_fr['Quote'] = 'Devis'

_ar['New Customer Quote'] = 'عرض سعر عميل جديد'
_fr['New Customer Quote'] = 'Nouveau devis client'

_ar['Create Quote'] = 'إنشاء عرض السعر'
_fr['Create Quote'] = 'Créer le devis'

_ar['Add Delivery Note'] = 'إضافة إشعار تسليم'
_fr['Add Delivery Note'] = 'Ajouter un bon de livraison'

_ar['No delivery notes yet.'] = 'لا توجد إشعارات تسليم بعد.'
_fr['No delivery notes yet.'] = 'Aucun bon de livraison pour l\'instant.'

_ar['New Delivery Note'] = 'إشعار تسليم جديد'
_fr['New Delivery Note'] = 'Nouveau bon de livraison'

_ar['-- Select Order --'] = '-- اختر الطلب --'
_fr['-- Select Order --'] = '-- Sélectionner une commande --'

_ar['Delivered Items'] = 'المواد المسلمة'
_fr['Delivered Items'] = 'Articles livrés'

_ar['Create Delivery Note'] = 'إنشاء إشعار التسليم'
_fr['Create Delivery Note'] = 'Créer le bon de livraison'

_ar['Admin Panel'] = 'لوحة الإدارة'
_fr['Admin Panel'] = 'Panneau d\'administration'

_ar['Total Companies'] = 'إجمالي الشركات'
_fr['Total Companies'] = 'Total des sociétés'

_ar['Total Users'] = 'إجمالي المستخدمين'
_fr['Total Users'] = 'Total des utilisateurs'

_ar['Active Companies'] = 'الشركات النشطة'
_fr['Active Companies'] = 'Sociétés actives'

_ar['Company Management'] = 'إدارة الشركات'
_fr['Company Management'] = 'Gestion des sociétés'

_ar['New Company'] = 'شركة جديدة'
_fr['New Company'] = 'Nouvelle société'

_ar['Manage'] = 'إدارة'
_fr['Manage'] = 'Gérer'

_ar['No companies registered yet.'] = 'لم يتم تسجيل شركات بعد.'
_fr['No companies registered yet.'] = 'Aucune société enregistrée pour l\'instant.'

_ar['Create Your First Company'] = 'إنشاء أول شركة لك'
_fr['Create Your First Company'] = 'Créer votre première société'

_ar['Quick Guide'] = 'دليل سريع'
_fr['Quick Guide'] = 'Guide rapide'

_ar['Create a Company'] = 'إنشاء شركة'
_fr['Create a Company'] = 'Créer une société'

_ar['Company Admin Login'] = 'تسجيل دخول مدير الشركة'
_fr['Company Admin Login'] = 'Connexion admin société'

_ar['Manage Resources'] = 'إدارة الموارد'
_fr['Manage Resources'] = 'Gérer les ressources'

_ar['Click New Company and fill in the company details, legal IDs, and admin credentials.'] = 'انقر على "شركة جديدة" واملأ تفاصيل الشركة والمعرفات القانونية وبيانات المدير.'
_fr['Click New Company and fill in the company details, legal IDs, and admin credentials.'] = 'Cliquez sur "Nouvelle société" et remplissez les détails, les identifiants légaux et les informations de l\'administrateur.'

_ar['The newly created admin can log in at /web/auth/login with the credentials you set.'] = 'يمكن لمدير الشركة الجديد تسجيل الدخول في /web/auth/login باستخدام البيانات التي حددتها.'
_fr['The newly created admin can log in at /web/auth/login with the credentials you set.'] = 'Le nouvel administrateur peut se connecter sur /web/auth/login avec les identifiants définis.'

_ar['Each company admin manages their own products, orders, and invoices fully isolated from other companies.'] = 'كل مدير شركة يدير منتجاته وطلباته وفواتيره بشكل منفصل عن الشركات الأخرى.'
_fr['Each company admin manages their own products, orders, and invoices fully isolated from other companies.'] = 'Chaque administrateur gère ses propres produits, commandes et factures, totalement isolés des autres sociétés.'

_ar['Click Users on any company to see all users belonging to that company.'] = 'انقر على "المستخدمين" في أي شركة لرؤية جميع المستخدمين التابعين لتلك الشركة.'
_fr['Click Users on any company to see all users belonging to that company.'] = 'Cliquez sur "Utilisateurs" dans une société pour voir tous les utilisateurs de cette société.'

_ar['All Companies'] = 'جميع الشركات'
_fr['All Companies'] = 'Toutes les sociétés'

_ar['Companies'] = 'الشركات'
_fr['Companies'] = 'Sociétés'

_ar['Movements'] = 'الحركات'
_fr['Movements'] = 'Mouvements'

_ar['Revenue'] = 'الإيرادات'
_fr['Revenue'] = 'Revenu'

_ar['No companies yet.'] = 'لا توجد شركات بعد.'
_fr['No companies yet.'] = 'Aucune société pour l\'instant.'

_ar['Create Company'] = 'إنشاء شركة'
_fr['Create Company'] = 'Créer une société'

_ar['Company Information'] = 'معلومات الشركة'
_fr['Company Information'] = 'Informations société'

_ar['Company Name'] = 'اسم الشركة'
_fr['Company Name'] = 'Nom de la société'

_ar['Street, building, etc.'] = 'الشارع، المبنى، إلخ.'
_fr['Street, building, etc.'] = 'Rue, immeuble, etc.'

_ar['Casablanca'] = 'الدار البيضاء'
_fr['Casablanca'] = 'Casablanca'

_ar['Website'] = 'الموقع الإلكتروني'
_fr['Website'] = 'Site web'

_ar['Contact Person'] = 'جهة الاتصال'
_fr['Contact Person'] = 'Personne à contacter'

_ar['Contact person'] = 'جهة الاتصال'
_fr['Contact person'] = 'Personne à contacter'

_ar['Contact Email'] = 'البريد الإلكتروني للاتصال'
_fr['Contact Email'] = 'E-mail de contact'

_ar['Moroccan Legal IDs'] = 'المعرفات القانونية المغربية'
_fr['Moroccan Legal IDs'] = 'Identifiants légaux marocains'

_ar['IF'] = 'IF'
_fr['IF'] = 'IF'

_ar['CNSS'] = 'CNSS'
_fr['CNSS'] = 'CNSS'

_ar['Patente'] = 'Patente'
_fr['Patente'] = 'Patente'

_ar['Company Admin User'] = 'مستخدم مدير الشركة'
_fr['Company Admin User'] = 'Utilisateur admin société'

_ar['Admin Name'] = 'اسم المدير'
_fr['Admin Name'] = 'Nom de l\'administrateur'

_ar['Admin Email'] = 'البريد الإلكتروني للمدير'
_fr['Admin Email'] = 'E-mail de l\'administrateur'

_ar['Admin Password'] = 'كلمة مرور المدير'
_fr['Admin Password'] = 'Mot de passe de l\'administrateur'

_ar['e.g. John Doe'] = 'مثال: أحمد محمد'
_fr['e.g. John Doe'] = 'ex. Jean Dupont'

_ar['Edit Company'] = 'تعديل الشركة'
_fr['Edit Company'] = 'Modifier la société'

_ar['Leave empty to keep current logo.'] = 'اتركه فارغاً للاحتفاظ بالشعار الحالي.'
_fr['Leave empty to keep current logo.'] = 'Laissez vide pour conserver le logo actuel.'

_ar['Save Changes'] = 'حفظ التغييرات'
_fr['Save Changes'] = 'Enregistrer les modifications'

_ar['Company Info'] = 'معلومات الشركة'
_fr['Company Info'] = 'Infos société'

_ar['Legal IDs'] = 'المعرفات القانونية'
_fr['Legal IDs'] = 'Identifiants légaux'

_ar['No legal IDs registered.'] = 'لا توجد معرفات قانونية مسجلة.'
_fr['No legal IDs registered.'] = 'Aucun identifiant légal enregistré.'

_ar['Danger Zone'] = 'منطقة الخطر'
_fr['Danger Zone'] = 'Zone dangereuse'

_ar['Delete this company and all associated data permanently.'] = 'احذف هذه الشركة وجميع البيانات المرتبطة بها نهائياً.'
_fr['Delete this company and all associated data permanently.'] = 'Supprimez cette société et toutes ses données associées définitivement.'

_ar['Delete Company'] = 'حذف الشركة'
_fr['Delete Company'] = 'Supprimer la société'

_ar['Overview'] = 'نظرة عامة'
_fr['Overview'] = 'Aperçu général'

_ar['No products.'] = 'لا توجد منتجات.'
_fr['No products.'] = 'Aucun produit.'

_ar['No orders.'] = 'لا توجد طلبات.'
_fr['No orders.'] = 'Aucune commande.'

_ar['No invoices.'] = 'لا توجد فواتير.'
_fr['No invoices.'] = 'Aucune facture.'

_ar['Add User'] = 'إضافة مستخدم'
_fr['Add User'] = 'Ajouter un utilisateur'

_ar['Full name'] = 'الاسم الكامل'
_fr['Full name'] = 'Nom complet'

_ar['User'] = 'مستخدم'
_fr['User'] = 'Utilisateur'

_ar['Admin'] = 'مدير'
_fr['Admin'] = 'Administrateur'

_ar['No users.'] = 'لا يوجد مستخدمون.'
_fr['No users.'] = 'Aucun utilisateur.'

_ar['Joined'] = 'تاريخ الانضمام'
_fr['Joined'] = 'Date d\'inscription'

_ar['Back to Companies'] = 'العودة إلى الشركات'
_fr['Back to Companies'] = 'Retour aux sociétés'

_ar['No users for this company.'] = 'لا يوجد مستخدمون لهذه الشركة.'
_fr['No users for this company.'] = 'Aucun utilisateur pour cette société.'

_ar['User Management'] = 'إدارة المستخدمين'
_fr['User Management'] = 'Gestion des utilisateurs'

_ar['All Users'] = 'جميع المستخدمين'
_fr['All Users'] = 'Tous les utilisateurs'

_ar['Search name or email...'] = 'البحث بالاسم أو البريد الإلكتروني...'
_fr['Search name or email...'] = 'Rechercher par nom ou e-mail...'

_ar['No users found.'] = 'لم يتم العثور على مستخدمين.'
_fr['No users found.'] = 'Aucun utilisateur trouvé.'

_ar['Try a different search term.'] = 'جرّب مصطلح بحث مختلف.'
_fr['Try a different search term.'] = 'Essayez un terme de recherche différent.'

_ar['Edit User'] = 'تعديل المستخدم'
_fr['Edit User'] = 'Modifier l\'utilisateur'

_ar['User Details'] = 'بيانات المستخدم'
_fr['User Details'] = 'Détails de l\'utilisateur'

_ar['Full Name'] = 'الاسم الكامل'
_fr['Full Name'] = 'Nom complet'

_ar['Reset Password'] = 'إعادة تعيين كلمة المرور'
_fr['Reset Password'] = 'Réinitialiser le mot de passe'

_ar['New Password'] = 'كلمة المرور الجديدة'
_fr['New Password'] = 'Nouveau mot de passe'

_ar['Min 8 characters'] = '8 أحرف على الأقل'
_fr['Min 8 characters'] = 'Min 8 caractères'

_ar['Delete User'] = 'حذف المستخدم'
_fr['Delete User'] = 'Supprimer l\'utilisateur'

_ar['Remove this user permanently.'] = 'احذف هذا المستخدم نهائياً.'
_fr['Remove this user permanently.'] = 'Supprimez cet utilisateur définitivement.'



