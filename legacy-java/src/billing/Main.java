package billing;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.math.BigDecimal;

/**
 * Reads invoices from stdin and prints one result line per invoice.
 *
 * Input format:
 *   INVOICE id|customerType|region|daysLate
 *   ITEM sku|qty|unitPrice
 *   ...
 *   END
 *
 * Output format:
 *   id|subtotal|discount|shipping|tax|lateFee|total
 *   id|ERROR|message
 */
public class Main {

    public static void main(String[] args) throws Exception {
        BufferedReader in = new BufferedReader(new InputStreamReader(System.in, "UTF-8"));
        InvoiceCalculator calculator = new InvoiceCalculator();
        Invoice current = null;
        String line;
        while ((line = in.readLine()) != null) {
            line = line.trim();
            if (line.isEmpty() || line.startsWith("#")) {
                continue;
            }
            if (line.startsWith("INVOICE ")) {
                String[] p = line.substring(8).split("\\|", -1);
                current = new Invoice(p[0], p[1], p[2], Integer.parseInt(p[3]));
            } else if (line.startsWith("ITEM ")) {
                String[] p = line.substring(5).split("\\|", -1);
                current.addItem(new LineItem(p[0], Integer.parseInt(p[1]), new BigDecimal(p[2])));
            } else if (line.equals("END")) {
                System.out.println(format(calculator, current));
                current = null;
            }
        }
    }

    private static String format(InvoiceCalculator calculator, Invoice invoice) {
        try {
            InvoiceCalculator.Result r = calculator.calculate(invoice);
            return invoice.getId() + "|" + r.subtotal.toPlainString() + "|" + r.discount.toPlainString()
                    + "|" + r.shipping.toPlainString() + "|" + r.tax.toPlainString()
                    + "|" + r.lateFee.toPlainString() + "|" + r.total.toPlainString();
        } catch (IllegalArgumentException e) {
            return invoice.getId() + "|ERROR|" + e.getMessage();
        }
    }
}
