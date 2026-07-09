import { useState, useRef, useEffect } from "react";
import { createPortal } from "react-dom";
import { Icon } from "@iconify/react";
import styles from "./Select.module.scss";

export interface SelectOption {
  value: string;
  label: string;
}

interface Props {
  options: SelectOption[];
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  wrapperClassName?: string;
  triggerClassName?: string;
  optionClassName?: string;
  maxHeight?: number;
  disabled?: boolean;
}

export const Select = ({
  options,
  value,
  onChange,
  placeholder,
  wrapperClassName,
  triggerClassName,
  optionClassName,
  maxHeight = 180,
  disabled = false,
}: Props) => {
  const [open, setOpen] = useState(false);
  const [dropdownPos, setDropdownPos] = useState({ top: 0, left: 0, width: 0 });
  const ref = useRef<HTMLDivElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const isMobile = window.innerWidth < 768;

  const selected = options.find((o) => o.value === value);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      // mobile closes via the backdrop's onClick instead (avoids iOS click/mousedown race)
      if (isMobile) return;
      if (
        ref.current &&
        !ref.current.contains(e.target as Node) &&
        dropdownRef.current &&
        !dropdownRef.current.contains(e.target as Node)
      ) {
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
      setDropdownPos({
        top: rect.bottom + 4,
        left: rect.left,
        width: rect.width,
      });
    }
  };

  const handleOpen = () => {
    if (disabled) return;
    updatePosition();
    setOpen((prev) => !prev);
  };

  const handleSelect = (optionValue: string) => {
    onChange(optionValue);
    setOpen(false);
  };

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
        ref={dropdownRef}
        data-portal-dropdown="true"
        style={
          isMobile
            ? undefined
            : {
                position: "fixed",
                top: dropdownPos.top,
                left: dropdownPos.left,
                width: dropdownPos.width,
                maxHeight,
                overflowY: "auto",
                zIndex: 1000,
              }
        }
      >
        {options.length === 0 ? (
          <div className={styles.empty}>No options</div>
        ) : (
          options.map((option) => (
            <button
              key={option.value}
              type="button"
              className={`${styles.option} ${optionClassName ?? ""} ${option.value === value ? styles.optionSelected : ""}`}
              onClick={() => handleSelect(option.value)}
            >
              {option.label}
              {option.value === value && (
                <Icon
                  icon="ph:check"
                  width={14}
                  height={14}
                  className={styles.checkIcon}
                />
              )}
            </button>
          ))
        )}
      </div>
    </>
  ) : null;

  return (
    <div ref={ref} className={`${styles.wrapper} ${wrapperClassName ?? ""}`}>
      <button
        type="button"
        className={`${styles.trigger} ${triggerClassName ?? ""} ${open ? styles.triggerOpen : ""} ${disabled ? styles.disabled : ""}`}
        onClick={handleOpen}
      >
        <span
          className={selected ? styles.triggerValue : styles.triggerPlaceholder}
        >
          {selected?.label ?? placeholder ?? "Select..."}
        </span>
        {!disabled && (
          <Icon
            icon={open ? "ph:caret-up" : "ph:caret-down"}
            width={14}
            height={14}
            className={styles.arrow}
          />
        )}
      </button>

      {createPortal(dropdown, document.body)}
    </div>
  );
};
