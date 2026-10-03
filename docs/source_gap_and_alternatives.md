# Additional source gap and alternatives

**Checked:** 2026-10-02 (Asia/Bangkok)

## Scope

I read `docs/dataset_source_validation.md` and `docs/source_audit.md` before searching. This note evaluates only additional leads; it does not repeat or revise the three prior candidate decisions. No listing website was crawled, no large dataset was downloaded, and nobody was contacted. I reviewed publisher documentation, terms, a published aggregate sample, and current dataset catalogs.

A source qualifies only when its provenance is distinct and documented, reuse rights cover the project use, and actual Hanoi apartment rental records can be selected from fields or an authorized sample. A row of aggregate metrics is not a listing record. Dataset mirrors and alternate copies do not create additional sources.

## Ranked additional candidates

| Rank | Candidate | Evidence of Hanoi apartment rental records | Rights and provenance | Decision |
|---:|---|---|---|---|
| 1 | **Nest Living agency inventory / research export** | Its Hanoi Rent Index says it summarizes the agency's own live inventory, currently reporting 399 homes, of which 385 are included in figures; 279 are categorized as apartments and rents are monthly. It separates studios, serviced apartments, villas, and whole houses. This verifies a promising source-level pool, but the public CSV is aggregate-only and no individual listing sample/schema was available in the reviewed export. | Nest Living says listing facts come from property owners/managers and the agency checks/corrects them. That is a separate agency corpus, but no research reuse license or permission for row-level export is documented. Its terms prohibit automated harvesting and copying listings/text/photos for another listing site or advertisement. No access was attempted beyond the published page. | **CONDITIONAL** - best new source to pursue through a written, research-specific, owner-authorized export/feed. Do not copy or harvest public listings under current evidence. |
| 2 | **Inside Airbnb Hanoi listings** | The official current download catalog has no Hanoi or Vietnam region. The provider's files are short-term Airbnb listings; even if a Hanoi snapshot were later added, that would be vacation/short-stay inventory and would not automatically represent the project's ordinary monthly apartment rental segment. | The catalog states CC BY 4.0 and requires attribution. It also asks users not to scrape the site or republish data, and says archived or new-city requests may be refused or assessed. Provenance is the Inside Airbnb project and its Airbnb listing snapshots, not a separate feed of ordinary lease listings. | **REJECT for the present project** - no current Hanoi file in the official catalog, and the observed product is short-term rental data. Reconsider only if Hanoi data and a use matching the project scope are documented. |

## Candidate 1 details: Nest Living

The [Hanoi Rent Index](https://nestliving.vn/rent-index) reports monthly asking rents from one agency's own Hanoi inventory, explicitly says it is not representative of the full Hanoi market, and lists **279 apartments** in its category breakdown. The page also reports studios separately (88), plus smaller counts for serviced apartments, villas, and whole houses. Its displayed index was regenerated on 2026-09-10; the site says the current catalogue moved into its system over a few weeks in mid-2026, so it does not provide a historical series.

The page offers a CSV, but describes it as **one row per aggregate cell** with a count of homes, suppression/publication indicator, and capture time. It is not a row-level listing export: no individual listing IDs, URLs, unit addresses, or individual price-area-bedroom records are exposed in that file description. The public page therefore supports a promising inventory count, not a claim that a reusable record-level dataset is available.

The [terms of use](https://nestliving.vn/terms) identify Nest Living as the residential leasing agency and say listing rent, size, and availability come from owners or managers and are checked/corrected by the agency. They prohibit automated harvesting and copying listing content for another listing site or advertisement. The terms do not grant a research-data license. Any row-level source would need to be supplied under explicit written permission covering storage and analysis; the supplied data should also exclude owner/tenant contact details. Because no sample rows or research license were available, this remains **CONDITIONAL**.

## Candidate 2 details: Inside Airbnb

The [official download catalog](https://insideairbnb.com/get-the-data/) says current free files cover listed regions and the last year, identifies listing/calendar/review file formats, and declares a **CC BY 4.0** license. The catalog was checked for both Hanoi and Vietnam; neither appears. The [data policies](https://insideairbnb.com/data-policies/) ask users not to scrape the project site or republish its data and direct users to request archived/new-region data where applicable.

The catalog's absence of Vietnam means there is no current Hanoi dataset to sample or validate. Further, Inside Airbnb concerns short-term Airbnb accommodations; its listing taxonomy can identify property/room type, but that does not make nightly vacation listings interchangeable with long-term monthly apartment rentals. It is **REJECTED** as a qualifying source for the current project. The CC BY statement does not cure the missing geography or the segment mismatch.

## Duplicate and non-source screening

Search results also surfaced Hugging Face copies of the TiniX corpus. For example, [vduydong/vietnam-real-estates-2](https://huggingface.co/datasets/vduydong/vietnam-real-estates-2) identifies the TiniX dataset as its source. Those copies are excluded: they repeat the already reviewed TiniX provenance and do not count as new sources. Similarly, a publisher mirror, converted format, aggregate index, or notebook using a dataset is not an independent listing corpus.

## Gap and safest practical next step

**No additional ACCEPT candidate was verified.** Nest Living is the strongest new lead because its own published index documents hundreds of Hanoi homes, monthly rents, and an apartment count, but the currently downloadable file contains only aggregates and its terms do not grant a research license for listing records. Inside Airbnb has no current Hanoi/Vietnam download and concerns short-term stays.

The safest practical next step is to seek a small, de-identified, owner-authorized research export from a Hanoi agency with a written permission basis, using Nest Living's documented inventory as a candidate lead. If that is unavailable, use records supplied directly by owners/managers who explicitly authorize research use. For either route, require a sample schema and a few permissioned rows first, verify Hanoi/apartment/monthly-rent fields, record provider and collection dates, and deduplicate against known sources before counting it as a distinct input. No outreach was made as part of this task.
