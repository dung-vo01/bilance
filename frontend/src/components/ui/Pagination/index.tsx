import { Icon } from "@iconify/react";
import { Select } from "@/components/ui/Select";
import styles from "./Pagination.module.scss";

const DEFAULT_PAGE_SIZE_OPTIONS = [10, 25, 50];

interface Props {
  page: number;
  totalPages: number;
  total: number;
  onChange: (page: number) => void;
  pageSize: number;
  onPageSizeChange: (pageSize: number) => void;
  pageSizeOptions?: number[];
}

export const Pagination = ({
  page,
  totalPages,
  total,
  onChange,
  pageSize,
  onPageSizeChange,
  pageSizeOptions = DEFAULT_PAGE_SIZE_OPTIONS,
}: Props) => {
  if (total === 0) return null;

  return (
    <div className={styles.pagination}>
      <div className={styles.pageSizeRow}>
        <span className={styles.pageSizeLabel}>Per page</span>
        <Select
          wrapperClassName={styles.pageSizeSelect}
          triggerClassName={styles.pageSizeTrigger}
          value={pageSize.toString()}
          onChange={(v) => onPageSizeChange(Number(v))}
          options={pageSizeOptions.map((n) => ({
            value: n.toString(),
            label: n.toString(),
          }))}
        />
      </div>

      <span className={styles.summary}>
        Page {page} of {totalPages} &middot; {total} total
      </span>

      {totalPages > 1 && (
        <div className={styles.controls}>
          <button
            type="button"
            className={styles.pageBtn}
            disabled={page <= 1}
            onClick={() => onChange(page - 1)}
          >
            <Icon icon="ph:caret-left" width={16} height={16} />
            Prev
          </button>
          <button
            type="button"
            className={styles.pageBtn}
            disabled={page >= totalPages}
            onClick={() => onChange(page + 1)}
          >
            Next
            <Icon icon="ph:caret-right" width={16} height={16} />
          </button>
        </div>
      )}
    </div>
  );
};
