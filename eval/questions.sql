-- Evaluation set: 30 questions with gold SQL (10 easy, 12 medium, 8 hard).
-- Format: "-- Q<id> | <level> | <question>" then the gold SQL.
-- These questions are deliberately different from context/examples.sql.

-- Q01 | easy | มีสาขาทั้งหมดกี่สาขา
SELECT COUNT(*) AS Branches FROM Branch;

-- Q02 | easy | How many Drive Thru branches are there?
SELECT COUNT(*) AS Drive_Thru_Branches FROM Branch WHERE Store_Type = 'Drive Thru';

-- Q03 | easy | มีเมนูเครื่องดื่มที่ยังขายอยู่กี่รายการ
SELECT COUNT(*) AS Active_Beverages FROM Product WHERE Type_Product = 'Beverage' AND Is_Active = 1;

-- Q04 | easy | What is the most expensive product?
SELECT Product_Name, Base_Price FROM Product ORDER BY Base_Price DESC LIMIT 1;

-- Q05 | easy | สมาชิกที่ถูกแบนมีกี่คน
SELECT COUNT(*) AS Banned_Members FROM Member WHERE Member_Status = 'Banned';

-- Q06 | easy | How many orders were cancelled in September 2026?
SELECT COUNT(*) AS Cancelled_Orders
FROM Orders
WHERE Order_Status = 'Cancelled'
  AND Order_DateTime >= '2026-09-01' AND Order_DateTime < '2026-10-01';

-- Q07 | easy | ยอดขายสุทธิเมื่อวานของทุกสาขารวมกัน
SELECT SUM(Net_Sales) AS Net_Sales_Yesterday FROM v_daily_branch_sales WHERE Sales_Date = '2026-09-29';

-- Q08 | easy | Which branches are under renovation?
SELECT Branch_Name FROM Branch WHERE Branch_Status = 'Renovation';

-- Q09 | easy | มีบัตร Starbucks Card ที่ถูกบล็อกกี่ใบ
SELECT COUNT(*) AS Blocked_Cards FROM Starbucks_Card WHERE Card_Status = 'Blocked';

-- Q10 | easy | How many members registered in 2026?
SELECT COUNT(*) AS New_Members
FROM Member
WHERE Registration_Date >= '2026-01-01' AND Registration_Date < '2026-10-01';

-- Q11 | medium | ยอดขายสุทธิของแต่ละประเภทออเดอร์ในเดือนกันยายน 2026
SELECT Order_Type, SUM(Net_Amount) AS Net_Sales
FROM v_order_summary
WHERE Order_Status <> 'Cancelled'
  AND Order_DateTime >= '2026-09-01' AND Order_DateTime < '2026-10-01'
GROUP BY Order_Type
ORDER BY Net_Sales DESC;

-- Q12 | medium | What was the revenue for each payment method in 2026?
SELECT Payment_Method, SUM(Amount) AS Revenue
FROM Payment
WHERE Payment_Status = 'Success'
  AND Paid_At >= '2026-01-01' AND Paid_At < '2026-10-01'
GROUP BY Payment_Method
ORDER BY Revenue DESC;

-- Q13 | medium | เมนูอาหารที่ขายได้จำนวนชิ้นมากที่สุด 5 อันดับในปี 2026
SELECT p.Product_Name, SUM(i.Quantity) AS Units
FROM Order_Item i
JOIN Orders o  ON o.Order_ID = i.Order_ID
JOIN Product p ON p.Product_ID = i.Product_ID
WHERE p.Type_Product = 'Food'
  AND o.Order_Status <> 'Cancelled'
  AND o.Order_DateTime >= '2026-01-01' AND o.Order_DateTime < '2026-10-01'
GROUP BY p.Product_ID, p.Product_Name
ORDER BY Units DESC
LIMIT 5;

-- Q14 | medium | What is the average net order value for each store type over the last 3 months?
SELECT Store_Type, ROUND(AVG(Net_Amount), 2) AS Avg_Net_Order_Value
FROM v_order_summary
WHERE Order_Status <> 'Cancelled'
  AND Order_DateTime >= '2026-07-01' AND Order_DateTime < '2026-10-01'
GROUP BY Store_Type;

-- Q15 | medium | สาขาไหนมีออเดอร์ถูกยกเลิกมากที่สุด 5 อันดับ
SELECT b.Branch_Name, COUNT(*) AS Cancelled_Orders
FROM Orders o
JOIN Branch b ON b.Branch_ID = o.Branch_ID
WHERE o.Order_Status = 'Cancelled' AND o.Order_DateTime < '2026-10-01'
GROUP BY b.Branch_ID, b.Branch_Name
ORDER BY Cancelled_Orders DESC
LIMIT 5;

-- Q16 | medium | How many orders and how much net sales did each month of 2026 have?
SELECT DATE_FORMAT(Sales_Date, '%Y-%m') AS Month, SUM(Orders) AS Orders, SUM(Net_Sales) AS Net_Sales
FROM v_daily_branch_sales
WHERE Sales_Date BETWEEN '2026-01-01' AND '2026-09-30'
GROUP BY DATE_FORMAT(Sales_Date, '%Y-%m')
ORDER BY Month;

-- Q17 | medium | ลูกค้า Gold กับ Green จ่ายเงินเฉลี่ยต่อออเดอร์เท่าไร
SELECT m.Member_Level, ROUND(AVG(p.Amount), 2) AS Avg_Paid_Per_Order
FROM Orders o
JOIN Member m  ON m.Member_ID = o.Member_ID
JOIN Payment p ON p.Order_ID = o.Order_ID AND p.Payment_Status = 'Success'
WHERE o.Order_Status <> 'Cancelled' AND o.Order_DateTime < '2026-10-01'
GROUP BY m.Member_Level;

-- Q18 | medium | Which 10 members spent the most money in 2026?
SELECT m.Member_Name, SUM(p.Amount) AS Total_Spent
FROM Orders o
JOIN Member m  ON m.Member_ID = o.Member_ID
JOIN Payment p ON p.Order_ID = o.Order_ID AND p.Payment_Status = 'Success'
WHERE o.Order_Status <> 'Cancelled'
  AND o.Order_DateTime >= '2026-01-01' AND o.Order_DateTime < '2026-10-01'
GROUP BY m.Member_ID, m.Member_Name
ORDER BY Total_Spent DESC
LIMIT 10;

-- Q19 | medium | แต่ละโปรโมชันให้ส่วนลดไปรวมเท่าไร
SELECT pr.Promotion_Name, SUM(r.Discount) AS Total_Discount
FROM Orders o
JOIN Promotion pr ON pr.Promotion_ID = o.Promotion_ID
JOIN Receipt r    ON r.Order_ID = o.Order_ID
WHERE o.Order_Status <> 'Cancelled' AND o.Order_DateTime < '2026-10-01'
GROUP BY pr.Promotion_ID, pr.Promotion_Name
ORDER BY Total_Discount DESC;

-- Q20 | medium | What percentage of orders in 2026 were delivery orders?
SELECT ROUND(100 * SUM(Order_Type = 'Delivery') / COUNT(*), 1) AS Delivery_Share_Pct
FROM Orders
WHERE Order_Status <> 'Cancelled'
  AND Order_DateTime >= '2026-01-01' AND Order_DateTime < '2026-10-01';

-- Q21 | medium | 5 สาขาที่จัดส่งเดลิเวอรีใช้เวลาเฉลี่ยนานที่สุด
SELECT b.Branch_Name,
       ROUND(AVG(TIMESTAMPDIFF(MINUTE, o.Order_DateTime, d.Delivered_At)), 1) AS Avg_Delivery_Minutes
FROM Delivery d
JOIN Orders o ON o.Order_ID = d.Order_ID
JOIN Branch b ON b.Branch_ID = o.Branch_ID
WHERE d.Delivery_Status = 'Delivered'
  AND o.Order_Status <> 'Cancelled'
  AND o.Order_DateTime < '2026-10-01'
GROUP BY b.Branch_ID, b.Branch_Name
ORDER BY Avg_Delivery_Minutes DESC
LIMIT 5;

-- Q22 | medium | How many points were earned and redeemed in September 2026?
SELECT Txn_Type, SUM(Points_Change) AS Points
FROM Point_Transaction
WHERE Txn_Type IN ('Earn', 'Redeem')
  AND Created_At >= '2026-09-01' AND Created_At < '2026-10-01'
GROUP BY Txn_Type;

-- Q23 | hard | 5 สาขาที่ยอดขายสุทธิเดือนกันยายนโตจากเดือนสิงหาคมมากที่สุดกี่เปอร์เซ็นต์
WITH m AS (
    SELECT Branch_ID, Branch_Name,
           SUM(CASE WHEN Sales_Date <  '2026-09-01' THEN Net_Sales ELSE 0 END) AS Aug_Sales,
           SUM(CASE WHEN Sales_Date >= '2026-09-01' THEN Net_Sales ELSE 0 END) AS Sep_Sales
    FROM v_daily_branch_sales
    WHERE Sales_Date BETWEEN '2026-08-01' AND '2026-09-30'
    GROUP BY Branch_ID, Branch_Name
)
SELECT Branch_Name, Aug_Sales, Sep_Sales,
       ROUND(100 * (Sep_Sales - Aug_Sales) / Aug_Sales, 1) AS Growth_Pct
FROM m
WHERE Aug_Sales > 0
ORDER BY Growth_Pct DESC
LIMIT 5;

-- Q24 | hard | For each store type, which product sold the most units in the last 6 months?
WITH sp AS (
    SELECT b.Store_Type, p.Product_Name, SUM(i.Quantity) AS Units
    FROM Orders o
    JOIN Branch b     ON b.Branch_ID = o.Branch_ID
    JOIN Order_Item i ON i.Order_ID = o.Order_ID
    JOIN Product p    ON p.Product_ID = i.Product_ID
    WHERE o.Order_Status <> 'Cancelled'
      AND o.Order_DateTime >= '2026-04-01' AND o.Order_DateTime < '2026-10-01'
    GROUP BY b.Store_Type, p.Product_ID, p.Product_Name
),
r AS (
    SELECT sp.*, RANK() OVER (PARTITION BY Store_Type ORDER BY Units DESC) AS Rnk
    FROM sp
)
SELECT Store_Type, Product_Name, Units FROM r WHERE Rnk = 1 ORDER BY Store_Type;

-- Q25 | hard | ลูกค้าที่เคยสั่งมากกว่า 20 ออเดอร์ แต่ไม่ได้สั่งเลยในเดือนกันยายน 2026 มีกี่คน
SELECT COUNT(*) AS Quiet_Regulars
FROM (
    SELECT Member_ID
    FROM Orders
    WHERE Order_Status <> 'Cancelled' AND Order_DateTime < '2026-10-01'
    GROUP BY Member_ID
    HAVING COUNT(*) > 20 AND SUM(Order_DateTime >= '2026-09-01') = 0
) t;

-- Q26 | hard | Which day of the week has the highest average daily net sales?
WITH d AS (
    SELECT Sales_Date, SUM(Net_Sales) AS Day_Sales
    FROM v_daily_branch_sales
    WHERE Sales_Date <= '2026-09-30'
    GROUP BY Sales_Date
)
SELECT DAYNAME(Sales_Date) AS Weekday, ROUND(AVG(Day_Sales), 2) AS Avg_Daily_Net_Sales
FROM d
GROUP BY DAYNAME(Sales_Date)
ORDER BY Avg_Daily_Net_Sales DESC
LIMIT 1;

-- Q27 | hard | ยอดขายสุทธิรายเดือนของปี 2026 พร้อมยอดสะสม
WITH m AS (
    SELECT DATE_FORMAT(Sales_Date, '%Y-%m') AS Month, SUM(Net_Sales) AS Net_Sales
    FROM v_daily_branch_sales
    WHERE Sales_Date BETWEEN '2026-01-01' AND '2026-09-30'
    GROUP BY DATE_FORMAT(Sales_Date, '%Y-%m')
)
SELECT Month, Net_Sales, SUM(Net_Sales) OVER (ORDER BY Month) AS Running_Total
FROM m
ORDER BY Month;

-- Q28 | hard | What percentage of members who ordered in August 2026 also ordered in September 2026?
WITH aug AS (
    SELECT DISTINCT Member_ID FROM Orders
    WHERE Order_Status <> 'Cancelled'
      AND Order_DateTime >= '2026-08-01' AND Order_DateTime < '2026-09-01'
),
sep AS (
    SELECT DISTINCT Member_ID FROM Orders
    WHERE Order_Status <> 'Cancelled'
      AND Order_DateTime >= '2026-09-01' AND Order_DateTime < '2026-10-01'
)
SELECT ROUND(100 * COUNT(sep.Member_ID) / COUNT(*), 1) AS Retention_Pct
FROM aug
LEFT JOIN sep ON sep.Member_ID = aug.Member_ID;

-- Q29 | hard | 3 สาขาที่มีสัดส่วนออเดอร์ที่ใช้โปรโมชันสูงที่สุดในปี 2026
SELECT b.Branch_Name,
       ROUND(100 * SUM(o.Promotion_ID IS NOT NULL) / COUNT(*), 1) AS Promo_Order_Pct
FROM Orders o
JOIN Branch b ON b.Branch_ID = o.Branch_ID
WHERE o.Order_Status <> 'Cancelled'
  AND o.Order_DateTime >= '2026-01-01' AND o.Order_DateTime < '2026-10-01'
GROUP BY b.Branch_ID, b.Branch_Name
ORDER BY Promo_Order_Pct DESC
LIMIT 3;

-- Q30 | hard | Which branch had the highest net sales on a single day in 2026, and on which date?
SELECT Branch_Name, Sales_Date, Net_Sales
FROM v_daily_branch_sales
WHERE Sales_Date BETWEEN '2026-01-01' AND '2026-09-30'
ORDER BY Net_Sales DESC
LIMIT 1;
