import { useState } from "react";
import { Icon } from "@iconify/react";
import { useCategoryBreakdown } from "@/hooks/queries";
import { DonutChart } from "@/components/ui/DonutChart";
import styles from "./CategoryBreakdownCard.module.scss";

const PALETTE = [
  "#10b981",
  "#3b82f6",
  "#f59e0b",
  "#8b5cf6",
  "#ec4899",
  "#14b8a6",
  "#f97316",
];
const OTHER_COLOR = "#94a3b8";
const MAX_SLICES = 7;

const PERIODS = [
  { label: "7 days", days: 7 as const },
  { label: "30 days", days: 30 as const },
];

interface Props {
  expenseGroupId?: number;
}

export const CategoryBreakdownCard = ({ expenseGroupId }: Props) => {
  const [days, setDays] = useState<7 | 30>(30);
  const { data, isLoading } = useCategoryBreakdown(days, expenseGroupId);

  const categories = data?.categories ?? [];
  const total = data?.total ?? 0;

  const top = categories.slice(0, MAX_SLICES);
  const rest = categories.slice(MAX_SLICES);
  const otherTotal = rest.reduce((sum, c) => sum + c.total, 0);

  const legendItems = [
    ...top.map((c, i) => ({ ...c, color: PALETTE[i % PALETTE.length] })),
    ...(otherTotal > 0
      ? [
          {
            category_id: null,
            category_name: "Other",
            total: otherTotal,
            percentage: total ? (otherTotal / total) * 100 : 0,
            color: OTHER_COLOR,
          },
        ]
      : []),
  ];

  const segments = legendItems.map((item) => ({
    label: item.category_name,
    value: item.total,
    color: item.color,
  }));

  return (
    <div className={styles.section}>
      <div className={styles.sectionHeader}>
        <h2 className={styles.sectionTitle}>Spending by category</h2>
        <div className={styles.periodToggle}>
          {PERIODS.map((p) => (
            <button
              key={p.days}
              className={`${styles.periodBtn} ${days === p.days ? styles.periodBtnActive : ""}`}
              onClick={() => setDays(p.days)}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {isLoading ? (
        <div className={styles.loading}>
          <Icon
            icon="ph:circle-notch"
            width={20}
            height={20}
            className={styles.spin}
          />
        </div>
      ) : categories.length === 0 ? (
        <div className={styles.empty}>
          <Icon icon="ph:chart-pie" width={32} height={32} />
          <p>
            No {expenseGroupId ? "group" : "personal"} expenses in the last{" "}
            {days} days
          </p>
        </div>
      ) : (
        <div className={styles.breakdownLayout}>
          <DonutChart
            segments={segments}
            centerValue={`€${total.toFixed(0)}`}
            centerLabel={`last ${days}d`}
          />
          <div className={styles.legend}>
            {legendItems.map((item) => (
              <div key={item.category_name} className={styles.legendItem}>
                <span
                  className={styles.legendSwatch}
                  style={{ background: item.color }}
                />
                <span className={styles.legendLabel}>{item.category_name}</span>
                <span className={styles.legendValue}>
                  €{item.total.toFixed(2)}
                </span>
                <span className={styles.legendPercent}>
                  {item.percentage.toFixed(0)}%
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
