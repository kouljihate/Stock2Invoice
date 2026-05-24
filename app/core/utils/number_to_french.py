def number_to_french(n):
    if n == 0:
        return "z\u00e9ro dirhams"
    units = ["", "un", "deux", "trois", "quatre", "cinq", "six", "sept", "huit", "neuf",
             "dix", "onze", "douze", "treize", "quatorze", "quinze", "seize",
             "dix-sept", "dix-huit", "dix-neuf"]
    tens = ["", "", "vingt", "trente", "quarante", "cinquante", "soixante",
            "soixante-dix", "quatre-vingt", "quatre-vingt-dix"]

    def _below_1000(num):
        if num == 0:
            return ""
        parts = []
        hundreds = num // 100
        remainder = num % 100
        if hundreds == 1:
            parts.append("cent")
        elif hundreds > 1:
            if remainder == 0:
                parts.append(units[hundreds] + " cents")
            else:
                parts.append(units[hundreds] + " cent")
        if remainder > 0:
            if remainder < 20:
                parts.append(units[remainder])
            else:
                ten = remainder // 10
                unit = remainder % 10
                if ten == 7 or ten == 9:
                    base = tens[ten - 1]
                    if unit == 1:
                        parts.append(base + " et " + units[10 + unit])
                    else:
                        parts.append(base + "-" + units[10 + unit] if unit > 0 else base + "-dix")
                elif ten == 8:
                    if unit > 0:
                        parts.append(tens[ten] + "-" + units[unit])
                    else:
                        parts.append("quatre-vingts")
                else:
                    if unit == 1:
                        parts.append(tens[ten] + " et un")
                    elif unit > 0:
                        parts.append(tens[ten] + "-" + units[unit])
                    else:
                        parts.append(tens[ten])
        return " ".join(parts)

    int_part = int(n)
    dec_part = round((n - int_part) * 100)

    result = []
    if int_part >= 1000000:
        millions = int_part // 1000000
        remainder_m = int_part % 1000000
        if millions == 1:
            result.append("un million")
        else:
            result.append(_below_1000(millions) + " millions")
        int_part = remainder_m

    if int_part >= 1000:
        thousands = int_part // 1000
        remainder_t = int_part % 1000
        if thousands == 1:
            result.append("mille")
        else:
            result.append(_below_1000(thousands) + " mille")
        int_part = remainder_t

    if int_part > 0:
        result.append(_below_1000(int_part))

    dirhams = " ".join(result).strip()
    if int(n) == 1:
        dirham_label = "dirham"
    else:
        dirham_label = "dirhams"
    if dec_part > 0:
        if dec_part == 1:
            cents = "un centime"
        else:
            cents = _below_1000(dec_part) + " centimes"
        return f"{dirhams} {dirham_label} et {cents}"
    return f"{dirhams} {dirham_label}"
