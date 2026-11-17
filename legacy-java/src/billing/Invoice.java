package billing;

import java.util.ArrayList;
import java.util.List;

public class Invoice {
    private final String id;
    private final String customerType; // RETAIL, WHOLESALE, GOV
    private final String region;       // EU, US, UA
    private final int daysLate;
    private final List<LineItem> items = new ArrayList<LineItem>();

    public Invoice(String id, String customerType, String region, int daysLate) {
        this.id = id;
        this.customerType = customerType;
        this.region = region;
        this.daysLate = daysLate;
    }

    public void addItem(LineItem item) {
        items.add(item);
    }

    public String getId() {
        return id;
    }

    public String getCustomerType() {
        return customerType;
    }

    public String getRegion() {
        return region;
    }

    public int getDaysLate() {
        return daysLate;
    }

    public List<LineItem> getItems() {
        return items;
    }
}
