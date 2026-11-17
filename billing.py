from decimal import Decimal, ROUND_HALF_UP, InvalidOperation

SHIPPING_FEE = Decimal("15.00")
FREE_SHIPPING_FROM = Decimal("200.00")
LATE_FEE_RATE = Decimal("0.015")
LATE_FEE_CAP = Decimal("0.10")


class InvoiceError(Exception):
    pass


class LineItem:
    def __init__(self, sku, qty, unit_price):
        self.sku = sku
        self.qty = qty
        self.unit_price = unit_price


class Invoice:
    def __init__(self, id_, customer_type, region, days_late):
        self.id = id_
        self.customer_type = customer_type
        self.region = region
        self.days_late = days_late
        self.items = []

    def add_item(self, item):
        self.items.append(item)


class Result:
    def __init__(self, subtotal, discount, shipping, tax, late_fee, total):
        self.subtotal = subtotal
        self.discount = discount
        self.shipping = shipping
        self.tax = tax
        self.late_fee = late_fee
        self.total = total


def _money(value):
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _volume_rate_for(qty):
    if qty >= 100:
        return Decimal("0.10")
    if qty >= 50:
        return Decimal("0.05")
    if qty >= 10:
        return Decimal("0.02")
    return Decimal("0")


def _type_discount_for(customer_type):
    if customer_type == "WHOLESALE":
        return Decimal("0.03")
    if customer_type == "GOV":
        return Decimal("0.05")
    if customer_type == "RETAIL":
        return Decimal("0")
    raise InvoiceError("Unknown customer type: " + customer_type)


def _tax_rate_for(region):
    if region == "EU":
        return Decimal("0.21")
    if region == "US":
        return Decimal("0.0725")
    if region == "UA":
        return Decimal("0.20")
    raise InvoiceError("Unknown region: " + region)


def calculate(invoice):
    tax_rate = _tax_rate_for(invoice.region)
    type_rate = _type_discount_for(invoice.customer_type)

    gross = _money(Decimal("0"))
    volume_discount = _money(Decimal("0"))
    for item in invoice.items:
        if item.qty <= 0:
            raise InvoiceError("Invalid quantity: " + str(item.qty))
        line_gross = _money(item.unit_price * Decimal(item.qty))
        line_discount = _money(line_gross * _volume_rate_for(item.qty))
        gross = gross + line_gross
        volume_discount = volume_discount + line_discount

    after_volume = gross - volume_discount
    type_discount = _money(after_volume * type_rate)
    discount = volume_discount + type_discount
    net = gross - discount

    shipping = _money(Decimal("0"))
    if invoice.items and net < FREE_SHIPPING_FROM:
        shipping = SHIPPING_FEE

    us = invoice.region == "US"
    if us and invoice.customer_type == "GOV":
        tax_rate = Decimal("0")
    tax_base = net if us else net + shipping
    tax = _money(tax_base * tax_rate)

    base = net + shipping + tax
    late_fee = _money(Decimal("0"))
    if invoice.days_late > 0:
        periods = (invoice.days_late + 29) // 30
        fee = _money(base * LATE_FEE_RATE * Decimal(periods))
        cap = _money(base * LATE_FEE_CAP)
        late_fee = cap if fee > cap else fee

    total = base + late_fee
    return Result(gross, discount, shipping, tax, late_fee, total)


def _plain(d):
    return format(d, "f")


def _java_int(s):
    # Mirrors Integer.parseInt: optional sign followed by ASCII digits only.
    t = s
    if t[:1] in ("+", "-"):
        body = t[1:]
    else:
        body = t
    if not body or not all("0" <= c <= "9" for c in body):
        raise ValueError("For input string: \"" + s + "\"")
    return int(t)


def _java_decimal(s):
    try:
        return Decimal(s)
    except (InvalidOperation, ValueError):
        raise ValueError("Character " + (s[:1] or " ") + " is neither a decimal digit number, decimal point, nor \"e\" notation exponential mark.")


def _format(invoice):
    try:
        r = calculate(invoice)
        return (invoice.id + "|" + _plain(r.subtotal) + "|" + _plain(r.discount)
                + "|" + _plain(r.shipping) + "|" + _plain(r.tax)
                + "|" + _plain(r.late_fee) + "|" + _plain(r.total))
    except InvoiceError as e:
        return invoice.id + "|ERROR|" + str(e)


def run(input_text):
    out = []
    current = None
    for raw in input_text.split("\n"):
        line = raw.strip()
        if line == "" or line.startswith("#"):
            continue
        if line.startswith("INVOICE "):
            p = line[8:].split("|")
            current = Invoice(p[0], p[1], p[2], _java_int(p[3]))
        elif line.startswith("ITEM "):
            p = line[5:].split("|")
            current.add_item(LineItem(p[0], _java_int(p[1]), _java_decimal(p[2])))
        elif line == "END":
            out.append(_format(current))
            current = None
    if not out:
        return ""
    return "\n".join(out) + "\n"
