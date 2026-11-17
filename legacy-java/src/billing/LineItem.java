package billing;

import java.math.BigDecimal;

public class LineItem {
    private final String sku;
    private final int qty;
    private final BigDecimal unitPrice;

    public LineItem(String sku, int qty, BigDecimal unitPrice) {
        this.sku = sku;
        this.qty = qty;
        this.unitPrice = unitPrice;
    }

    public String getSku() {
        return sku;
    }

    public int getQty() {
        return qty;
    }

    public BigDecimal getUnitPrice() {
        return unitPrice;
    }
}
