/** Normalize user-entered domain to bare hostname (matches API). */
export function normalizeSiteDomainInput(domain: string): string {
  let value = domain.trim().toLowerCase();
  for (const prefix of ["https://", "http://"]) {
    if (value.startsWith(prefix)) {
      value = value.slice(prefix.length);
    }
  }
  return value.split("/")[0]?.split("?")[0]?.replace(/\.$/, "") ?? value;
}

export type SiteFormValues = {
  domain: string;
  site_name: string;
  primary_locale: string;
  target_countries: string;
  target_languages: string;
  industry: string;
  business_model: string;
};

export const EMPTY_SITE_FORM: SiteFormValues = {
  domain: "",
  site_name: "",
  primary_locale: "zh-TW",
  target_countries: "TW",
  target_languages: "zh-TW",
  industry: "",
  business_model: "",
};

export function siteToFormValues(site: {
  domain: string;
  site_name: string;
  primary_locale?: string;
  target_countries?: string[];
  target_languages?: string[];
  industry?: string | null;
  business_model?: string | null;
}): SiteFormValues {
  return {
    domain: site.domain,
    site_name: site.site_name,
    primary_locale: site.primary_locale ?? "zh-TW",
    target_countries: (site.target_countries ?? ["TW"]).join(", "),
    target_languages: (site.target_languages ?? ["zh-TW"]).join(", "),
    industry: site.industry ?? "",
    business_model: site.business_model ?? "",
  };
}

export function formValuesToPayload(values: SiteFormValues) {
  const splitList = (raw: string) =>
    raw
      .split(/[,，\s]+/)
      .map((s) => s.trim())
      .filter(Boolean);

  return {
    domain: normalizeSiteDomainInput(values.domain),
    site_name: values.site_name.trim(),
    primary_locale: values.primary_locale.trim() || "zh-TW",
    target_countries: splitList(values.target_countries),
    target_languages: splitList(values.target_languages),
    industry: values.industry.trim() || null,
    business_model: values.business_model.trim() || null,
  };
}
