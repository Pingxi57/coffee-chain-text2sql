-- Few-shot examples for the prompt. Adapted from coffee-chain-database/queries/02_analytics.sql.
-- Format: a "-- Question:" line, then the correct SQL.

-- Question: ยอดขายสุทธิของทุกสาขารวมกันวันนี้
SELECT SUM(Net_Sales) AS Net_Sales_Today
FROM v_daily_branch_sales
WHERE Sales_Date = '2026-09-30';

-- Question: How many active Gold members are there?
SELECT COUNT(*) AS Active_Gold_Members
FROM Member
WHERE Member_Level = 'Gold' AND Member_Status = 'Active';

-- Question: รายได้รายเดือนในปี 2026 และเติบโตจากเดือนก่อนกี่เปอร์เซ็นต์
WITH monthly AS (
    SELECT DATE_FORMAT(Paid_At, '%Y-%m') AS Month, SUM(Amount) AS Revenue
    FROM Payment
    WHERE Payment_Status = 'Success'
      AND Paid_At >= '2026-01-01' AND Paid_At < '2026-10-01'
    GROUP BY DATE_FORMAT(Paid_At, '%Y-%m')
)
SELECT Month,
       Revenue,
       ROUND(100 * (Revenue - LAG(Revenue) OVER (ORDER BY Month))
                 / LAG(Revenue) OVER (ORDER BY Month), 1) AS Growth_Pct
FROM monthly
ORDER BY Month;

-- Question: Which 10 branches made the most revenue in the last 12 months?
SELECT b.Branch_Name, b.Store_Type, COUNT(*) AS Orders, SUM(p.Amount) AS Revenue
FROM Orders o
JOIN Payment p ON p.Order_ID = o.Order_ID AND p.Payment_Status = 'Success'
JOIN Branch b  ON b.Branch_ID = o.Branch_ID
WHERE o.Order_DateTime >= '2025-10-01' AND o.Order_DateTime < '2026-10-01'
GROUP BY b.Branch_ID, b.Branch_Name, b.Store_Type
ORDER BY Revenue DESC
LIMIT 10;

-- Question: เมนูขายดี 3 อันดับแรกของแต่ละสาขาในช่วง 6 เดือนล่าสุด
WITH branch_product AS (
    SELECT o.Branch_ID, i.Product_ID, SUM(i.Quantity) AS Units
    FROM Orders o
    JOIN Order_Item i ON i.Order_ID = o.Order_ID
    WHERE o.Order_Status <> 'Cancelled'
      AND o.Order_DateTime >= '2026-04-01' AND o.Order_DateTime < '2026-10-01'
    GROUP BY o.Branch_ID, i.Product_ID
),
ranked AS (
    SELECT bp.*,
           DENSE_RANK() OVER (PARTITION BY bp.Branch_ID ORDER BY bp.Units DESC) AS Rank_In_Branch
    FROM branch_product bp
)
SELECT b.Branch_Name, r.Rank_In_Branch, p.Product_Name, r.Units
FROM ranked r
JOIN Branch b  ON b.Branch_ID = r.Branch_ID
JOIN Product p ON p.Product_ID = r.Product_ID
WHERE r.Rank_In_Branch <= 3
ORDER BY b.Branch_Name, r.Rank_In_Branch;

-- Question: What is the busiest hour at each branch over the last 3 months?
WITH hourly AS (
    SELECT Branch_ID, HOUR(Order_DateTime) AS Hr, COUNT(*) AS Orders
    FROM Orders
    WHERE Order_Status <> 'Cancelled'
      AND Order_DateTime >= '2026-07-01' AND Order_DateTime < '2026-10-01'
    GROUP BY Branch_ID, HOUR(Order_DateTime)
),
ranked AS (
    SELECT h.*, ROW_NUMBER() OVER (PARTITION BY Branch_ID ORDER BY Orders DESC, Hr) AS rn
    FROM hourly h
)
SELECT b.Branch_Name,
       CONCAT(LPAD(r.Hr, 2, '0'), ':00-', LPAD(r.Hr + 1, 2, '0'), ':00') AS Busiest_Hour,
       r.Orders
FROM ranked r
JOIN Branch b ON b.Branch_ID = r.Branch_ID
WHERE r.rn = 1
ORDER BY r.Orders DESC;

-- Question: สินค้าอะไรที่ลูกค้ามักซื้อคู่กัน
SELECT pa.Product_Name AS Product_A,
       pb.Product_Name AS Product_B,
       COUNT(DISTINCT a.Order_ID) AS Orders_Together
FROM Order_Item a
JOIN Order_Item b ON b.Order_ID = a.Order_ID AND a.Product_ID < b.Product_ID
JOIN Product pa   ON pa.Product_ID = a.Product_ID
JOIN Product pb   ON pb.Product_ID = b.Product_ID
GROUP BY pa.Product_Name, pb.Product_Name
ORDER BY Orders_Together DESC
LIMIT 15;
