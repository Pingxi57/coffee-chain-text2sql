# Business rules for the coffee-chain database

## Dates
- The dataset ends on 2026-09-30. Treat 2026-09-30 as "today".
  - "this month" = September 2026, "last month" = August 2026, "this year" = 2026.
  - Never use CURDATE(), NOW() or CURRENT_DATE. Write literal dates instead.
  - Ignore anything after 2026-09-30 (demo orders).
- Filter datetimes with ranges, e.g. Order_DateTime >= '2026-09-01' AND Order_DateTime < '2026-10-01',
  not DATE(Order_DateTime) = ..., so indexes can be used.
- v_promotion_status computes status from the real current date, so do NOT use it for
  "active" promotions. Use Start_Date <= '2026-09-30' AND End_Date >= '2026-09-30' on Promotion.

## Money
- Gross sales = Orders.Order_Amount (sum of item lines).
- Net sales = Gross sales - Receipt.Discount. "sales" or "ยอดขาย" means NET sales by default.
- Revenue / paid amount = Payment.Amount WHERE Payment_Status = 'Success'
  (net sales + delivery fee). "revenue" or "รายได้" means this.
- Exclude orders with Order_Status = 'Cancelled' unless the question asks about cancellations.

## Useful views
- v_daily_branch_sales: one row per branch per day (cancelled excluded): Orders, Gross_Sales, Discounts, Net_Sales.
- v_order_summary: one row per order with member, branch, promotion, amounts and payment method.
- v_product_sales and v_member_summary are ALL-TIME totals. For a date range, use the base tables.
- Units sold = SUM(Order_Item.Quantity).

## Values and Thai terms
- สาขา = Branch. Store_Type: 'Drive Thru' (ไดรฟ์ทรู), 'Coffee House'.
- เมนู / สินค้า = Product. Type_Product: 'Beverage' (เครื่องดื่ม), 'Food' (อาหาร), 'Merch' (สินค้าที่ระลึก).
- สมาชิก / ลูกค้า = Member. Member_Level: 'Green', 'Gold'. Member_Status: 'Active', 'Inactive', 'Banned'.
- ช่องทางชำระเงิน = Payment_Method: 'StarbucksCard', 'CreditCard', 'Cash', 'QR'.
- ประเภทออเดอร์ = Order_Type: 'InStorePickup' (รับที่ร้าน), 'OrderToTable' (สั่งที่โต๊ะ), 'Delivery' (เดลิเวอรี).

## Output
- Show readable names (Branch_Name, Product_Name, Member_Name), not only IDs.
- For "top N" questions use ORDER BY ... LIMIT N. When listing rows, LIMIT 100.
- MySQL has no MEDIAN(); use ROW_NUMBER() with COUNT() OVER if a median is needed.
