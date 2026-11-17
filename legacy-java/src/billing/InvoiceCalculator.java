package billing;

import java.math.BigDecimal;
import java.math.RoundingMode;

/**
 * Legacy invoice calculation. Business rules (some of them historical quirks):
 *  - volume discount per line: qty >= 100 -> 10%, qty >= 50 -> 5%, qty >= 10 -> 2%
 *  - customer type discount on the amount after volume discounts: WHOLESALE 3%, GOV 5%
 *  - shipping: flat 15.00 when net amount is below 200.00 (and the invoice has items)
 *  - tax: EU 21%, US 7.25%, UA 20%; shipping is NOT taxed in the US, taxed elsewhere;
 *    GOV customers are tax exempt in the US
 *  - late fee: 1.5% per started 30-day period of delay, on (net + shipping + tax),
 *    capped at 10% of that same base
 *  - every monetary step is rounded to 2 decimals, HALF_UP
 */
public class InvoiceCalculator {

    private static final BigDecimal SHIPPING_FEE = new BigDecimal("15.00");
    private static final BigDecimal FREE_SHIPPING_FROM = new BigDecimal("200.00");
    private static final BigDecimal LATE_FEE_RATE = new BigDecimal("0.015");
    private static final BigDecimal LATE_FEE_CAP = new BigDecimal("0.10");

    public static class Result {
        public final BigDecimal subtotal;
        public final BigDecimal discount;
        public final BigDecimal shipping;
        public final BigDecimal tax;
        public final BigDecimal lateFee;
        public final BigDecimal total;

        Result(BigDecimal subtotal, BigDecimal discount, BigDecimal shipping,
               BigDecimal tax, BigDecimal lateFee, BigDecimal total) {
            this.subtotal = subtotal;
            this.discount = discount;
            this.shipping = shipping;
            this.tax = tax;
            this.lateFee = lateFee;
            this.total = total;
        }
    }

    public Result calculate(Invoice invoice) {
        BigDecimal taxRate = taxRateFor(invoice.getRegion());
        BigDecimal typeRate = typeDiscountFor(invoice.getCustomerType());

        BigDecimal gross = money(BigDecimal.ZERO);
        BigDecimal volumeDiscount = money(BigDecimal.ZERO);
        for (LineItem item : invoice.getItems()) {
            if (item.getQty() <= 0) {
                throw new IllegalArgumentException("Invalid quantity: " + item.getQty());
            }
            BigDecimal lineGross = money(item.getUnitPrice().multiply(new BigDecimal(item.getQty())));
            BigDecimal lineDiscount = money(lineGross.multiply(volumeRateFor(item.getQty())));
            gross = gross.add(lineGross);
            volumeDiscount = volumeDiscount.add(lineDiscount);
        }

        BigDecimal afterVolume = gross.subtract(volumeDiscount);
        BigDecimal typeDiscount = money(afterVolume.multiply(typeRate));
        BigDecimal discount = volumeDiscount.add(typeDiscount);
        BigDecimal net = gross.subtract(discount);

        BigDecimal shipping = money(BigDecimal.ZERO);
        if (!invoice.getItems().isEmpty() && net.compareTo(FREE_SHIPPING_FROM) < 0) {
            shipping = SHIPPING_FEE;
        }

        boolean us = "US".equals(invoice.getRegion());
        if (us && "GOV".equals(invoice.getCustomerType())) {
            taxRate = BigDecimal.ZERO;
        }
        BigDecimal taxBase = us ? net : net.add(shipping);
        BigDecimal tax = money(taxBase.multiply(taxRate));

        BigDecimal base = net.add(shipping).add(tax);
        BigDecimal lateFee = money(BigDecimal.ZERO);
        if (invoice.getDaysLate() > 0) {
            int periods = (invoice.getDaysLate() + 29) / 30;
            BigDecimal fee = money(base.multiply(LATE_FEE_RATE).multiply(new BigDecimal(periods)));
            BigDecimal cap = money(base.multiply(LATE_FEE_CAP));
            lateFee = fee.compareTo(cap) > 0 ? cap : fee;
        }

        BigDecimal total = base.add(lateFee);
        return new Result(gross, discount, shipping, tax, lateFee, total);
    }

    private static BigDecimal money(BigDecimal value) {
        return value.setScale(2, RoundingMode.HALF_UP);
    }

    private static BigDecimal volumeRateFor(int qty) {
        if (qty >= 100) {
            return new BigDecimal("0.10");
        }
        if (qty >= 50) {
            return new BigDecimal("0.05");
        }
        if (qty >= 10) {
            return new BigDecimal("0.02");
        }
        return BigDecimal.ZERO;
    }

    private static BigDecimal typeDiscountFor(String customerType) {
        if ("WHOLESALE".equals(customerType)) {
            return new BigDecimal("0.03");
        }
        if ("GOV".equals(customerType)) {
            return new BigDecimal("0.05");
        }
        if ("RETAIL".equals(customerType)) {
            return BigDecimal.ZERO;
        }
        throw new IllegalArgumentException("Unknown customer type: " + customerType);
    }

    private static BigDecimal taxRateFor(String region) {
        if ("EU".equals(region)) {
            return new BigDecimal("0.21");
        }
        if ("US".equals(region)) {
            return new BigDecimal("0.0725");
        }
        if ("UA".equals(region)) {
            return new BigDecimal("0.20");
        }
        throw new IllegalArgumentException("Unknown region: " + region);
    }
}
