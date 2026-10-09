/**
 * Standardized date & time formatting utilities for QuantumFraud.
 * Renders all timestamps explicitly in Asia/Kolkata (IST, UTC+05:30).
 */

export function formatISTDate(
  dateInput: string | number | Date | null | undefined,
  includeTime = true
): string {
  if (!dateInput) return 'N/A';

  try {
    let date: Date;
    if (typeof dateInput === 'string') {
      let s = dateInput.trim();
      // If ISO string lacks timezone indicator (e.g. "2026-10-09T14:30:00"), treat as UTC
      if (s.includes('T') && !s.endsWith('Z') && !/[+-]\d{2}:\d{2}$/.test(s)) {
        s = s + 'Z';
      }
      date = new Date(s);
    } else {
      date = new Date(dateInput);
    }

    if (isNaN(date.getTime())) {
      return 'N/A';
    }

    const options: Intl.DateTimeFormatOptions = {
      timeZone: 'Asia/Kolkata',
      year: 'numeric',
      month: 'short',
      day: '2-digit',
    };

    if (includeTime) {
      options.hour = '2-digit';
      options.minute = '2-digit';
      options.second = '2-digit';
      options.hour12 = true;
    }

    const formatted = new Intl.DateTimeFormat('en-IN', options).format(date);
    return `${formatted} IST`;
  } catch (e) {
    return 'N/A';
  }
}

export function formatISTTimeOnly(
  dateInput: string | number | Date | null | undefined
): string {
  if (!dateInput) return 'N/A';

  try {
    let date: Date;
    if (typeof dateInput === 'string') {
      let s = dateInput.trim();
      if (s.includes('T') && !s.endsWith('Z') && !/[+-]\d{2}:\d{2}$/.test(s)) {
        s = s + 'Z';
      }
      date = new Date(s);
    } else {
      date = new Date(dateInput);
    }

    if (isNaN(date.getTime())) {
      return 'N/A';
    }

    const formatted = new Intl.DateTimeFormat('en-IN', {
      timeZone: 'Asia/Kolkata',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: true,
    }).format(date);

    return `${formatted} IST`;
  } catch (e) {
    return 'N/A';
  }
}
