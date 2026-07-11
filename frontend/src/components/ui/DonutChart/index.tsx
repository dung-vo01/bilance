import styles from "./DonutChart.module.scss";

export interface DonutSegment {
  label: string;
  value: number;
  color: string;
}

interface Props {
  segments: DonutSegment[];
  size?: number;
  strokeWidth?: number;
  centerValue?: string;
  centerLabel?: string;
}

export const DonutChart = ({
  segments,
  size = 160,
  strokeWidth = 22,
  centerValue,
  centerLabel,
}: Props) => {
  const total = segments.reduce((sum, s) => sum + s.value, 0);
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;

  let cumulative = 0;

  const summary = segments
    .map((s) => `${s.label} ${Math.round((s.value / (total || 1)) * 100)}%`)
    .join(", ");

  return (
    <div className={styles.wrapper} style={{ width: size, height: size }}>
      <svg
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        role="img"
        aria-label={
          total > 0
            ? `Spending breakdown: ${summary}`
            : "No spending in this period"
        }
      >
        <g transform={`rotate(-90 ${size / 2} ${size / 2})`}>
          {total === 0 ? (
            <circle
              cx={size / 2}
              cy={size / 2}
              r={radius}
              fill="none"
              stroke="var(--color-border)"
              strokeWidth={strokeWidth}
            />
          ) : (
            segments.map((s) => {
              const fraction = s.value / total;
              const dash = fraction * circumference;
              const offset = -((cumulative / total) * circumference);
              cumulative += s.value;
              return (
                <circle
                  key={s.label}
                  cx={size / 2}
                  cy={size / 2}
                  r={radius}
                  fill="none"
                  stroke={s.color}
                  strokeWidth={strokeWidth}
                  strokeDasharray={`${dash} ${circumference - dash}`}
                  strokeDashoffset={offset}
                />
              );
            })
          )}
        </g>
      </svg>
      {(centerValue || centerLabel) && (
        <div className={styles.center}>
          {centerValue && (
            <span className={styles.centerValue}>{centerValue}</span>
          )}
          {centerLabel && (
            <span className={styles.centerLabel}>{centerLabel}</span>
          )}
        </div>
      )}
    </div>
  );
};
