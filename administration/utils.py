def amount_to_words(amount):
    """
    Converts a numeric amount (integer or float) into Indian Rupees words.
    Example: 10500 -> "Ten Thousand Five Hundred Rupees Only"
    """
    try:
        amount_int = int(amount)
    except (ValueError, TypeError):
        return "Zero Rupees Only"

    if amount_int == 0:
        return "Zero Rupees Only"

    units = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine"]
    teens = ["Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
    tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]

    def convert_below_thousand(n):
        res = []
        if n >= 100:
            res.append(units[n // 100] + " Hundred")
            n %= 100
        if n >= 20:
            res.append(tens[n // 10])
            n %= 10
        elif n >= 10:
            res.append(teens[n - 10])
            n = 0
        if n > 0:
            res.append(units[n])
        return " ".join(res)

    words = []

    # Crore (1,00,00,000)
    crore = amount_int // 10000000
    if crore > 0:
        words.append(convert_below_thousand(crore) + " Crore")
        amount_int %= 10000000

    # Lakh (1,00,000)
    lakh = amount_int // 100000
    if lakh > 0:
        words.append(convert_below_thousand(lakh) + " Lakh")
        amount_int %= 100000

    # Thousand (1,000)
    thousand = amount_int // 1000
    if thousand > 0:
        words.append(convert_below_thousand(thousand) + " Thousand")
        amount_int %= 1000

    # Hundreds and below
    if amount_int > 0:
        words.append(convert_below_thousand(amount_int))

    return " ".join(words).strip() + " Rupees Only"
