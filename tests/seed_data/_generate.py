# -*- coding: utf-8 -*-
"""Deterministic generator for the seed CSV files in this folder.

Usage:  python tests/seed_data/_generate.py
Writes pme_admins.csv, customers.csv and suppliers.csv next to itself.
"""
import csv
import io
import os
import random
import unicodedata

OUT = os.path.dirname(os.path.abspath(__file__))


def slug(text):
    n = unicodedata.normalize('NFKD', text)
    n = ''.join(c for c in n if not unicodedata.combining(c))
    keep = ''.join(c if c.isalnum() else '-' for c in n.lower())
    while '--' in keep:
        keep = keep.replace('--', '-')
    return keep.strip('-')


CITIES = [
    ('Casablanca', '20'), ('Rabat', '10'), ('Marrakech', '40'), ('Fes', '30'),
    ('Tanger', '90'), ('Agadir', '80'), ('Meknes', '50'), ('Oujda', '60'),
    ('Kenitra', '14'), ('Tetouan', '93'), ('Sale', '11'), ('Safi', '46'),
    ('El Jadida', '24'), ('Beni Mellal', '23'), ('Nador', '62'),
    ('Settat', '26'), ('Mohammedia', '28'), ('Khouribga', '25'),
]
CITY_CODES = dict(CITIES)
CITY_NAMES = ['Fès', 'Kénitra', 'Tétouan', 'Salé', 'Meknès',
              'Casablanca', 'Rabat', 'Marrakech', 'Tanger', 'Agadir',
              'Oujda', 'Safi', 'El Jadida', 'Beni Mellal', 'Nador',
              'Settat', 'Mohammedia', 'Khouribga']
STREETS = [
    'Rue Ibn Batouta', 'Avenue Mohammed V', 'Boulevard Zerktouni',
    'Rue Al Massira', 'Avenue Hassan II', 'Boulevard Mohammed VI',
    'Rue de la Liberté', 'Avenue des FAR', 'Rue Ibn Sina',
    'Boulevard Anfa', 'Rue Al Andalous', 'Avenue Moulay Youssef',
    'Rue Tarik Ibn Ziad', 'Boulevard de la Corniche', 'Rue Al Qods',
    'Avenue Abdelkrim El Khattabi', 'Rue Oued Sebou',
    'Boulevard Yacoub El Mansour',
]
QUARTIERS = [
    'Maarif', 'Hay Hassani', 'Ain Sebaa', 'Sidi Maarouf', 'Derb Sultan',
    'Hay Riad', 'Agdal', 'Gueliz', 'Malabata', 'Iberia', 'Hay Mohammadi',
    'Quartier Industriel', 'Zone Franche', 'Hay Salam', 'Al Qods',
]
FIRST = [
    'Youssef', 'Salma', 'Karim', 'Nadia', 'Hicham', 'Imane', 'Omar',
    'Fatima Zahra', 'Mehdi', 'Sanae', 'Anas', 'Ayoub', 'Btissam', 'Chaimae',
    'Driss', 'Ghita', 'Hamza', 'Ilyas', 'Jamal', 'Khadija', 'Laila',
    'Mohamed', 'Mounir', 'Nabil', 'Othmane', 'Rachid', 'Reda', 'Saad',
    'Soukaina', 'Tarik', 'Wafaa', 'Yassine', 'Zineb', 'Amine', 'Badr',
    'Chafik', 'Hind', 'Idriss', 'Kawtar', 'Loubna', 'Majda', 'Noureddine',
    'Oumaima', 'Yasmine', 'Zakaria', 'Abdelilah', 'Aicha', 'Brahim',
    'Faouzi', 'Hafsa', 'Soufiane', 'Hanane', 'Mustapha', 'Asmae',
]
LAST = [
    'El Amrani', 'Benjelloun', 'Ouazzani', 'El Fassi', 'Berrada', 'Tazi',
    'Benali', 'Alaoui', 'Chraibi', 'Bouzid', 'Bennani', 'Cherkaoui',
    'Daoudi', 'El Idrissi', 'El Khattabi', 'El Mansouri', 'Haddad', 'Hajji',
    'Jebli', 'Kabbaj', 'Lahlou', 'Lamrani', 'Maaouni', 'Naciri', 'Ouahbi',
    'Rahmani', 'Saidi', 'Sekkat', 'Skalli', 'Tahiri', 'Zeroual', 'Ziani',
    'Bakkali', 'Bouhlal', 'Chami', 'Drissi', 'El Ghazi', 'Erraji',
    'Guessous', 'Hamdi', 'Kettani', 'Mekouar', 'Naji', 'Sabri',
]
PREFIX = [
    'Atlas', 'Medina', 'Sahara', 'Rif', 'Souss', 'Anfa', 'Anoual', 'Bab',
    'Kasbah', 'Massira', 'Nahda', 'Firdaous', 'Oasis', 'Palmier', 'Yasmine',
    'Chams', 'Nour', 'Badr', 'Salam', 'Amal', 'Ittihad', 'Tawfiq', 'Najah',
    'Rayan', 'Al Wifaq', 'Al Fath', 'Zerktouni', 'Chaouia', 'Doukkala',
    'Tafilalet', 'Haouz', 'Loukkos', 'Draa', 'Bouregreg', 'Sebou',
    'Moulouya', 'Argan', 'Cedre', 'Menthe', 'Zaitoun',
]
CORE = [
    'Trading', 'Distribution', 'Textile', 'Agro', 'BTP', 'Electronique',
    'Logistique', 'Papeterie', 'Metallurgie', 'Plastique', 'Chimie',
    'Informatique', 'Transport', 'Froid', 'Menuiserie', 'Peinture',
    'Cosmetique', 'Pharmaceutique', 'Emballage', 'Imprimerie', 'Energie',
    'Solaire', 'Mobilier', 'Ceramique', 'Verrerie', 'Cuir', 'Alimentaire',
    'Quincaillerie', 'Outillage', 'Sanitaire',
]
SUFFIX = ['SARL', 'SARL AU', 'SA', 'SNC']
SUP_CORE = [
    'Materiel Industriel', 'Fournitures de Bureau', 'Composants Electroniques',
    'Papier et Carton', 'Emballages', 'Quincaillerie Generale',
    'Electricite Industrielle', 'Peintures et Revetements', 'Outillage Pro',
    'Aciers et Metaux', 'Bois et Panneaux', 'Textiles Techniques',
    'Produits Chimiques', 'Plastiques Techniques', 'Verrerie Laboratoire',
    'Cartonnage', 'Soudure et Robinetterie', 'Consommables Atelier',
    'Transport et Fret', 'Maintenance Industrielle', 'Eclairage LED',
    'Sanitaire et Plomberie', 'Menuiserie Aluminium', 'Toitures et Bardages',
    'Hygiene et Nettoyage', 'Securite et EPI', 'Filtration et Air',
]
TERMS = ['Comptant', 'Net 30', 'Net 45', 'Net 60', 'Net 90']
DOMAINS = ['gmail.com', 'menara.ma', 'outlook.fr', 'yahoo.fr', 'hotmail.com']

TENANTS = [
    ('Atlas Distribution SARL', 'Youssef El Amrani', 'atlas-distribution', 'Casablanca', '12 Rue Ibn Batouta'),
    ('Maroc Textile Industrie', 'Salma Benjelloun', 'maroc-textile', 'Fès', '45 Avenue Mohammed V'),
    ('Casablanca Agro Food', 'Karim Ouazzani', 'casa-agro', 'Casablanca', '8 Boulevard Zerktouni'),
    ('Rif Construction BTP', 'Nadia El Fassi', 'rif-construction', 'Tétouan', '23 Rue Al Massira'),
    ('Souss Electronique', 'Hicham Berrada', 'souss-electronique', 'Agadir', '37 Avenue Hassan II'),
    ('Fès Cuir et Maroquinerie', 'Imane Tazi', 'fes-cuir', 'Fès', '5 Rue de la Liberté'),
    ('Tanger Logistique Nord', 'Omar Benali', 'tanger-logistique', 'Tanger', '61 Boulevard Mohammed VI'),
    ('Ouarzazate Energie Solaire', 'Fatima Zahra Alaoui', 'ouarzazate-energie', 'Ouarzazate', '9 Avenue des FAR'),
    ('Agadir Peche Marine', 'Mehdi Chraibi', 'agadir-peche', 'Agadir', '14 Rue Ibn Sina'),
    ('Meknes Papeterie Moderne', 'Sanae Bouzid', 'meknes-papeterie', 'Meknès', '2 Boulevard Anfa'),
]


def phone(rnd):
    if rnd.random() < 0.55:
        return '+212 6{:02d} {:02d} {:02d} {:02d}'.format(
            rnd.randint(0, 99), rnd.randint(0, 99),
            rnd.randint(0, 99), rnd.randint(0, 99))
    return '+212 5{:02d} {:02d} {:02d} {:02d}'.format(
        rnd.randint(0, 99), rnd.randint(0, 99),
        rnd.randint(0, 99), rnd.randint(0, 99))


def address(rnd):
    return '{} {}, {}'.format(rnd.randint(1, 320),
                              rnd.choice(STREETS), rnd.choice(QUARTIERS))


def digits(rnd, n):
    return ''.join(str(rnd.randint(0, 9)) for _ in range(n))


def rc(rnd, code):
    return 'RC/{}/{}'.format(code, rnd.randint(100000, 999999))


def unique_emails(local_parts, domain):
    seen, out = set(), []
    for part in local_parts:
        base, n, cand = part, 1, part
        while cand in seen:
            n += 1
            cand = '{}{}'.format(base, n)
        seen.add(cand)
        out.append('{}@{}'.format(cand, domain))
    return out


def main():
    random.seed(20261102)

    admins, admin_rows = [], []
    for i, (company, owner, cslug, city, addr) in enumerate(TENANTS, start=1):
        code = CITY_CODES.get(slug(city), '20')
        parts = slug(owner).split('-')
        email = '{}.{}@{}.ma'.format(parts[0], parts[-1], cslug)
        admin_rows.append({
            'company_name': company,
            'company_slug': cslug,
            'company_email': 'contact@{}.ma'.format(cslug),
            'company_phone': phone(random),
            'company_city': city,
            'company_address': addr,
            'company_ice': digits(random, 15),
            'company_rc': rc(random, code),
            'company_if_tax': digits(random, 8),
            'company_cnss': str(random.randint(100000, 999999)),
            'company_patente': str(random.randint(10000, 99999)),
            'name': owner,
            'email': email,
            'password': 'Pme@{}!demo'.format(2026 + i),
            'roles': 'PME-Admin',
        })
        admins.append({'email': email, 'city': city, 'code': code})

    people = ['{} {}'.format(f, l) for f in FIRST for l in LAST]

    cust_rows = []
    for t_i, admin in enumerate(admins, start=1):
        rnd = random.Random(1000 * t_i)
        combos = ['{} {} {}'.format(p, c, s)
                  for p in PREFIX for c in CORE for s in SUFFIX]
        rnd.shuffle(combos)
        company_names = combos[:60]

        shuffled = list(people)
        rnd.shuffle(shuffled)
        private_names = shuffled[:40]

        kinds = ['company'] * 60 + ['prive'] * 40
        rnd.shuffle(kinds)
        c_it, p_it = iter(company_names), iter(private_names)

        names, contacts = [], []
        for kind in kinds:
            if kind == 'company':
                names.append(next(c_it))
                contacts.append(rnd.choice(shuffled))
            else:
                names.append(next(p_it))
                contacts.append('')

        locals_ = []
        for name in names:
            bits = slug(name).split('-')
            locals_.append('{}.{}'.format(bits[0], bits[-2])
                           if len(bits) > 2 else '.'.join(bits))
        emails = unique_emails(locals_, rnd.choice(DOMAINS))

        for idx, kind in enumerate(kinds):
            is_company = kind == 'company'
            city = admin['city'] if rnd.random() < 0.6 else rnd.choice(CITY_NAMES)
            cust_rows.append({
                'pme_admin_email': admin['email'],
                'type': kind,
                'name': names[idx],
                'contact': contacts[idx],
                'email': emails[idx],
                'phone': phone(rnd),
                'address': address(rnd),
                'city': city,
                'ICE': digits(rnd, 15) if is_company else '',
                'RC': rc(rnd, admin['code']) if is_company else '',
                'paiement_terms': rnd.choice(TERMS),
            })

    sup_rows = []
    for t_i, admin in enumerate(admins, start=1):
        rnd = random.Random(7000 * t_i)
        combos = ['{} {} {}'.format(p, c, s)
                  for p in PREFIX for c in SUP_CORE for s in SUFFIX]
        rnd.shuffle(combos)
        names = combos[:50]

        locals_ = []
        for name in names:
            bits = slug(name).split('-')
            locals_.append('{}.{}'.format(bits[0], bits[1])
                           if len(bits) > 2 else bits[0])
        emails = unique_emails(locals_, rnd.choice(DOMAINS))

        for idx, name in enumerate(names):
            city = admin['city'] if rnd.random() < 0.5 else rnd.choice(CITY_NAMES)
            sup_rows.append({
                'pme_admin_email': admin['email'],
                'name': name,
                'contact_name': rnd.choice(people),
                'email': emails[idx],
                'phone': phone(rnd),
                'address': address(rnd),
                'city': city,
                'ice': digits(rnd, 15),
                'rc': rc(rnd, admin['code']),
                'payment_terms': rnd.choice(TERMS),
            })

    def write(filename, rows, columns):
        with io.open(os.path.join(OUT, filename), 'w',
                     encoding='utf-8', newline='') as fh:
            writer = csv.DictWriter(fh, fieldnames=columns)
            writer.writeheader()
            for row in rows:
                writer.writerow({c: row[c] for c in columns})

    write('pme_admins.csv', admin_rows, [
        'company_name', 'company_slug', 'company_email', 'company_phone',
        'company_city', 'company_address', 'company_ice', 'company_rc',
        'company_if_tax', 'company_cnss', 'company_patente',
        'name', 'email', 'password', 'roles'])
    write('customers.csv', cust_rows, [
        'pme_admin_email', 'type', 'name', 'contact', 'email', 'phone',
        'address', 'city', 'ICE', 'RC', 'paiement_terms'])
    write('suppliers.csv', sup_rows, [
        'pme_admin_email', 'name', 'contact_name', 'email', 'phone',
        'address', 'city', 'ice', 'rc', 'payment_terms'])

    print('pme_admins={} customers={} suppliers={}'.format(
        len(admin_rows), len(cust_rows), len(sup_rows)))


if __name__ == '__main__':
    main()
