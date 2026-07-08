import { useState, useRef, useEffect } from "react";
import { createPortal } from "react-dom";
import { Icon } from "@iconify/react";
import styles from "./DatePicker.module.scss";
import { Select } from "../Select";

interface Props {
  value: string | null;
  onChange: (value: string) => void;
  label?: string;
  className?: string;
}

const DAYS = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"];
const MONTHS = [
  "January",
  "February",
  "March",
  "April",
  "May",
  "June",
  "July",
  "August",
  "September",
  "October",
  "November",
  "December",
];

export const DatePicker = ({ value, onChange, className }: Props) => {
  const ref = useRef<HTMLDivElement>(null);
  const [open, setOpen] = useState(false);
  const [dropdownPos, setDropdownPos] = useState({ top: 0, left: 0 });
  const isMobile = window.innerWidth < 768;

  const now = new Date();
  const date = value ? new Date(value) : new Date();

  const [viewYear, setViewYear] = useState(date.getFullYear());
  const [viewMonth, setViewMonth] = useState(date.getMonth());
  const [time, setTime] = useState(
    `${String(now.getHours()).padStart(2, "0")}:${String(now.getMinutes()).padStart(2, "0")}`,
  );

  const hours = Array.from({ length: 24 }, (_, i) => ({
    value: String(i).padStart(2, "0"),
    label: String(i).padStart(2, "0"),
  }));

  const minutes = Array.from({ length: 60 }, (_, i) => ({
    value: String(i).padStart(2, "0"),
    label: String(i).padStart(2, "0"),
  }));

  useEffect(() => {
    const d = value ? new Date(value) : new Date();
    setTime(
      `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`,
    );
    setViewYear(d.getFullYear());
    setViewMonth(d.getMonth());
  }, [value]);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      // On mobile, the full-screen backdrop's own onClick closes the picker
      // instead. Closing here on mousedown would unmount the backdrop before
      // iOS Safari's delayed synthetic click fires, letting that click fall
      // through onto whatever element ends up underneath.
      if (isMobile) return;
      const target = e.target as HTMLElement;
      // ignore clicks inside any portal dropdown
      if (target.closest('[data-portal-dropdown="true"]')) return;
      if (ref.current && !ref.current.contains(target)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useEffect(() => {
    if (!open) return;
    const handleScroll = () => updatePosition();
    window.addEventListener("scroll", handleScroll, true);
    return () => window.removeEventListener("scroll", handleScroll, true);
  }, [open]);

  const updatePosition = () => {
    if (ref.current) {
      const rect = ref.current.getBoundingClientRect();
      const dropdownHeight = 380; // approximate height of calendar + time
      const spaceBelow = window.innerHeight - rect.bottom;
      const openUpward = spaceBelow < dropdownHeight;

      setDropdownPos({
        top: openUpward ? rect.top - dropdownHeight - 4 : rect.bottom + 4,
        left: rect.left,
      });
    }
  };

  const handleOpen = () => {
    updatePosition();
    setOpen((p) => !p);
  };

  const getDaysInMonth = (year: number, month: number) =>
    new Date(year, month + 1, 0).getDate();

  const getFirstDayOfMonth = (year: number, month: number) =>
    new Date(year, month, 1).getDay();

  const handleDayClick = (day: number) => {
    const [h, m] = time.split(":").map(Number);
    const pad = (n: number) => String(n).padStart(2, "0");
    const local = `${viewYear}-${pad(viewMonth + 1)}-${pad(day)}T${pad(h)}:${pad(m)}:00`;
    onChange(local);
  };

  const handleTimeChange = (newTime: string) => {
    setTime(newTime);
    if (value) {
      const d = new Date(value);
      const [h, m] = newTime.split(":").map(Number);
      const pad = (n: number) => String(n).padStart(2, "0");
      const local = `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(h)}:${pad(m)}:00`;
      onChange(local);
    }
  };

  const prevMonth = () => {
    if (viewMonth === 0) {
      setViewMonth(11);
      setViewYear((y) => y - 1);
    } else setViewMonth((m) => m - 1);
  };

  const nextMonth = () => {
    if (viewMonth === 11) {
      setViewMonth(0);
      setViewYear((y) => y + 1);
    } else setViewMonth((m) => m + 1);
  };

  const selectedDate = value ? new Date(value) : null;
  const isSelected = (day: number) =>
    selectedDate &&
    selectedDate.getFullYear() === viewYear &&
    selectedDate.getMonth() === viewMonth &&
    selectedDate.getDate() === day;

  const isToday = (day: number) => {
    const today = new Date();
    return (
      today.getFullYear() === viewYear &&
      today.getMonth() === viewMonth &&
      today.getDate() === day
    );
  };

  const daysInMonth = getDaysInMonth(viewYear, viewMonth);
  const firstDay = getFirstDayOfMonth(viewYear, viewMonth);

  const displayValue = value
    ? new Date(value).toLocaleString("en-FI", {
        day: "numeric",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      })
    : "Select date & time";

  const dropdown = open ? (
    <>
      {isMobile && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0,0,0,0.4)",
            zIndex: 999,
          }}
          onClick={() => setOpen(false)}
        />
      )}
      <div
        className={styles.dropdown}
        data-portal-dropdown="true"
        style={
          isMobile
            ? undefined
            : {
                position: "fixed",
                top: dropdownPos.top,
                left: dropdownPos.left,
                zIndex: 1000,
              }
        }
      >
        <div className={styles.header}>
          <button type="button" onClick={prevMonth} className={styles.navBtn}>
            <Icon icon="ph:caret-left" width={16} height={16} />
          </button>
          <span className={styles.monthYear}>
            {MONTHS[viewMonth]} {viewYear}
          </span>
          <button type="button" onClick={nextMonth} className={styles.navBtn}>
            <Icon icon="ph:caret-right" width={16} height={16} />
          </button>
        </div>

        <div className={styles.grid}>
          {DAYS.map((d) => (
            <div key={d} className={styles.dayName}>
              {d}
            </div>
          ))}
          {Array.from({ length: firstDay }).map((_, i) => (
            <div key={`empty-${i}`} />
          ))}
          {Array.from({ length: daysInMonth }).map((_, i) => {
            const day = i + 1;
            return (
              <button
                key={day}
                type="button"
                onClick={() => handleDayClick(day)}
                className={`${styles.day} ${isSelected(day) ? styles.daySelected : ""} ${isToday(day) && !isSelected(day) ? styles.dayToday : ""}`}
              >
                {day}
              </button>
            );
          })}
        </div>

        <div className={styles.timeRow}>
          <Icon
            icon="ph:clock"
            width={16}
            height={16}
            className={styles.timeIcon}
          />
          <Select
            value={time.split(":")[0]}
            onChange={(h) => handleTimeChange(`${h}:${time.split(":")[1]}`)}
            options={hours}
            triggerClassName={styles.timeSelect}
            maxHeight={200}
          />
          <span className={styles.timeSep}>:</span>
          <Select
            value={time.split(":")[1]}
            onChange={(m) => handleTimeChange(`${time.split(":")[0]}:${m}`)}
            options={minutes}
            triggerClassName={styles.timeSelect}
            maxHeight={200}
          />
        </div>
      </div>
    </>
  ) : null;

  return (
    <div ref={ref} className={`${styles.wrapper} ${className ?? ""}`}>
      <button
        type="button"
        className={`${styles.trigger} ${open ? styles.triggerOpen : ""} ${!value ? styles.triggerPlaceholder : ""}`}
        onClick={handleOpen}
      >
        <Icon
          icon="ph:calendar"
          width={16}
          height={16}
          className={styles.calIcon}
        />
        <span>{displayValue}</span>
        <Icon
          icon={open ? "ph:caret-up" : "ph:caret-down"}
          width={14}
          height={14}
          className={styles.arrow}
        />
      </button>

      {createPortal(dropdown, document.body)}
    </div>
  );
};
