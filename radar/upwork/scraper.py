"""Playwright scraping for Upwork job search and detail pages."""

from __future__ import annotations

import logging
import re
from typing import Any
from urllib.parse import urlencode

from radar.connectors.types import RawListing, RawListingRef
from radar.upwork.api_extract import extract_jobs_from_payload, merge_job_items
from radar.upwork.config import PAGE_TIMEOUT_MS, SEARCH_BASE_URL
from radar.upwork.errors import ExtractionError
from radar.upwork.parse import canonical_job_url, parse_job_id_from_url, parse_listing_fields

logger = logging.getLogger(__name__)

JOB_TILE_SELECTOR = 'article[data-test="JobTile"], [data-test="job-tile"]'
JOB_LINK_SELECTOR = (
    'a[href*="~"], [data-test="job-tile-title-link"], [data-test="job-tile-title-link UpLink"]'
)

SEARCH_JOB_LINKS_JS = """
() => {
  const results = [];
  const seen = new Set();

  const textFrom = (root, selectors) => {
    for (const sel of selectors) {
      const el = root.querySelector(sel);
      if (el) {
        const value = (el.textContent || '').replace(/\\s+/g, ' ').trim();
        if (value) return value;
      }
    }
    return '';
  };

  const extractTileFields = (card) => {
    const budget = textFrom(card, [
      '[data-test="budget"]',
      '[data-test="JobBudget"]',
      '[data-test="job-type-label"] strong',
      '[data-test="job-type-label"]',
    ]);
    const jobType = textFrom(card, [
      '[data-test="job-type-label"]',
      '[data-test="JobTypeLabel"]',
    ]);
    const experienceLevel = textFrom(card, [
      '[data-test="experience-level"]',
      '[data-test="ExperienceLevel"]',
    ]);
    const postedTime = textFrom(card, [
      '[data-test="job-pubilshed-date"]',
      '[data-test="job-published-date"]',
      '[data-test="PostedOn"]',
    ]);
    const proposalCount = textFrom(card, [
      '[data-test="proposals-tier"]',
      '[data-test="ProposalsTier"]',
    ]);
    const tile = {};
    if (budget) tile.budget = budget;
    if (jobType) tile.job_type = jobType;
    if (experienceLevel) tile.experience_level = experienceLevel;
    if (postedTime) tile.posted_time = postedTime;
    if (proposalCount) tile.proposal_count = proposalCount;
    return tile;
  };

  const addJob = (id, title, href, card) => {
    if (!id || seen.has(id)) return;
    const cleanTitle = (title || '').replace(/\\s+/g, ' ').trim();
    if (!cleanTitle || cleanTitle.length < 3) return;
    seen.add(id);
    let url = href || '';
    if (url && !url.startsWith('http')) {
      url = 'https://www.upwork.com' + url;
    }
    if (!url) {
      url = 'https://www.upwork.com/jobs/~' + id;
    }
    const tile = card ? extractTileFields(card) : {};
    results.push({
      external_id: id,
      url: url.split('?')[0],
      title: cleanTitle,
      tile,
    });
  };

  const cards = document.querySelectorAll(
    'article[data-test="JobTile"], [data-test="job-tile"], section[data-test="JobTile"]'
  );
  for (const card of cards) {
    const titleEl = card.querySelector(
      '[data-test="job-tile-title-link"], [data-test="job-tile-title-link UpLink"], h2 a, h3 a, a[href*="~"]'
    );
    if (!titleEl) continue;
    const href = titleEl.getAttribute('href') || titleEl.href || '';
    const match = href.match(/~([0-9a-zA-Z]+)/);
    if (!match) continue;
    addJob(match[1], titleEl.textContent || '', href, card);
  }

  if (results.length === 0) {
    for (const a of document.querySelectorAll('a[href*="~"]')) {
      const href = a.getAttribute('href') || a.href || '';
      if (!/jobs|details|~/.test(href)) continue;
      const match = href.match(/~([0-9a-zA-Z]+)/);
      if (!match) continue;
      addJob(match[1], a.textContent || '', href, null);
    }
  }

  return results;
}
"""

EXTRACT_NUXT_JS = """
() => {
  const payload = window.__NUXT__ || window.__NEXT_DATA__ || null;
  if (!payload) return [];
  const text = JSON.stringify(payload);
  const results = [];
  const seen = new Set();
  const titlePattern = /"title":"((?:\\\\.|[^"\\\\]){3,200})"/g;
  const idPattern = /"~([0-9a-zA-Z]{10,})"/g;
  const titles = [...text.matchAll(titlePattern)].map((m) =>
    m[1].replace(/\\\\u002F/g, '/').replace(/\\\\"/g, '"')
  );
  const ids = [...text.matchAll(idPattern)].map((m) => m[1]);
  for (let i = 0; i < Math.min(titles.length, ids.length); i++) {
    const id = ids[i];
    if (seen.has(id)) continue;
    seen.add(id);
    results.push({
      external_id: id,
      title: titles[i],
      url: 'https://www.upwork.com/jobs/~' + id,
    });
  }
  return results;
}
"""

EXTRACT_JOB_JS = """
() => {
  const text = (sel) => {
    const el = document.querySelector(sel);
    return el ? el.textContent.replace(/\\s+/g, ' ').trim() : '';
  };
  const allText = (selectors) => {
    for (const sel of selectors) {
      const value = text(sel);
      if (value) return value;
    }
    return '';
  };

  const skills = [...document.querySelectorAll(
    '[data-test="Skill"] a, [data-test="skill"] a, .air3-token-wrap a, a[href*="/search/jobs/skill/"]'
  )]
    .map((el) => (el.textContent || '').trim())
    .filter((value, index, arr) => value && arr.indexOf(value) === index);

  const features = [...document.querySelectorAll(
    '[data-test="job-details"] li, [data-test="features"] li, .features li, ul.features li'
  )]
    .map((el) => (el.textContent || '').replace(/\\s+/g, ' ').trim())
    .filter(Boolean);

  const description = allText([
    '[data-test="Description"]',
    '[data-test="job-description"]',
    '.job-description',
    'div[id*="job-description"]',
    'section[data-test="Description"]',
  ]);

  const title = allText([
    '[data-test="job-title"]',
    'h1',
    '.job-title',
  ]);

  const budget = allText([
    '[data-test="budget"]',
    '[data-test="JobBudget"]',
    '[data-test="job-type-label"] strong',
  ]);
  const jobType = allText([
    '[data-test="job-type-label"]',
    '[data-test="JobTypeLabel"]',
  ]);
  const experienceLevel = allText([
    '[data-test="experience-level"]',
    '[data-test="ExperienceLevel"]',
  ]);
  const postedTime = allText([
    '[data-test="job-pubilshed-date"]',
    '[data-test="job-published-date"]',
    '[data-test="PostedOn"]',
  ]);
  const proposalCount = allText([
    '[data-test="proposals-tier"]',
    '[data-test="ProposalsTier"]',
  ]);
  const clientRating = allText([
    '[data-test="total-feedback"]',
    '[data-test="client-rating"]',
    '[data-test="feedback-score"]',
  ]);
  const clientSpend = allText([
    '[data-test="client-spend"]',
    '[data-test="total-spent"]',
  ]);
  const clientCountry = allText([
    '[data-test="client-country"]',
    '[data-test="LocationLabel"]',
    '[data-test="location"]',
  ]);
  const projectLength = allText([
    '[data-test="duration-label"]',
    '[data-test="project-length"]',
  ]);
  const category = allText([
    '[data-test="category"]',
    '[data-test="Category"]',
  ]);
  const subcategory = allText([
    '[data-test="subcategory"]',
    '[data-test="Subcategory"]',
  ]);
  const paymentVerified = !!document.querySelector(
    '[data-test="payment-verified"], [data-test="payment-verification-status"], [data-test="PaymentVerified"]'
  );

  return {
    title,
    description,
    skills,
    features,
    page_text: (document.body.innerText || '').slice(0, 12000),
    dom: {
      title,
      description,
      budget: budget || jobType,
      job_type: jobType,
      experience_level: experienceLevel,
      posted_time: postedTime,
      proposal_count: proposalCount,
      client_rating: clientRating,
      client_spend: clientSpend,
      client_country: clientCountry,
      project_length: projectLength,
      category,
      subcategory,
      skills,
      payment_verified: paymentVerified ? true : null,
    },
  };
}
"""

_API_URL_HINTS = (
    "graphql",
    "jobs/search",
    "marketplacejob",
    "visitorjob",
    "pub/job",
)


def build_search_url(query: str) -> str:
    params = urlencode({"q": query, "sort": "recency"})
    return f"{SEARCH_BASE_URL}?{params}"


def _should_capture_response(url: str) -> bool:
    lower = url.lower()
    return any(hint in lower for hint in _API_URL_HINTS)


def _extract_refs_from_page(page: Any) -> list[dict[str, Any]]:
    try:
        items = page.evaluate(SEARCH_JOB_LINKS_JS)
    except Exception as exc:
        raise ExtractionError(f"Failed to read Upwork search results: {exc}") from exc
    if not isinstance(items, list):
        items = []

    if not items:
        try:
            nuxt_items = page.evaluate(EXTRACT_NUXT_JS)
            if isinstance(nuxt_items, list):
                items = nuxt_items
        except Exception:
            pass

    return items if isinstance(items, list) else []


def _log_search_diagnostics(page: Any, query: str, url: str) -> None:
    try:
        title = page.title()
        current_url = page.url
        body_snippet = page.evaluate(
            "() => (document.body.innerText || '').replace(/\\s+/g, ' ').trim().slice(0, 400)"
        )
        tile_count = page.locator(JOB_TILE_SELECTOR).count()
        link_count = page.locator('a[href*="~"]').count()
        logger.warning(
            "Upwork search returned 0 jobs for query=%r url=%s page_title=%r tiles=%d links=%d snippet=%r",
            query,
            current_url,
            title,
            tile_count,
            link_count,
            body_snippet,
        )
        if re.search(r"verify you.?re human|captcha|access denied", str(body_snippet), re.I):
            logger.warning(
                "Upwork may be blocking automated search. Retry with visible Chrome "
                "(the default) or run: python -m radar upwork search --query %r --debug",
                query,
            )
    except Exception as exc:
        logger.warning("Could not collect Upwork search diagnostics: %s", exc)


def search_jobs(context: Any, query: str, limit: int, *, debug: bool = False) -> list[RawListingRef]:
    page = context.new_page()
    page.set_default_timeout(PAGE_TIMEOUT_MS)
    url = build_search_url(query)
    api_jobs: list[dict[str, str]] = []

    def on_response(response: Any) -> None:
        if response.status != 200 or not _should_capture_response(response.url):
            return
        try:
            payload = response.json()
        except Exception:
            return
        extracted = extract_jobs_from_payload(payload)
        if extracted:
            logger.debug("Captured %d jobs from API response: %s", len(extracted), response.url)
            api_jobs.extend(extracted)

    page.on("response", on_response)

    try:
        logger.info("Searching Upwork for query=%r limit=%d url=%s", query, limit, url)
        page.goto(url, wait_until="domcontentloaded")

        try:
            page.wait_for_selector(f"{JOB_TILE_SELECTOR}, {JOB_LINK_SELECTOR}", timeout=20_000)
        except Exception:
            logger.info("Job tile selector not found yet for query=%r; continuing", query)

        page.wait_for_timeout(3500)

        refs: list[RawListingRef] = []
        stagnant_rounds = 0
        previous_count = 0

        while len(refs) < limit and stagnant_rounds < 4:
            dom_items = _extract_refs_from_page(page)
            items = merge_job_items(api_jobs, dom_items)

            for item in items:
                external_id = item.get("external_id", "")
                job_url = item.get("url") or canonical_job_url(external_id)
                title = item.get("title", "")
                if not external_id:
                    continue
                if any(existing.external_id == external_id for existing in refs):
                    continue
                tile = item.get("tile") or {}
                extras = {"tile": tile} if isinstance(tile, dict) and tile else {}
                refs.append(
                    RawListingRef(
                        external_id=external_id,
                        url=job_url,
                        title=title,
                        source_query=query,
                        extras=extras,
                    )
                )
                if len(refs) >= limit:
                    break

            if len(refs) == previous_count:
                stagnant_rounds += 1
            else:
                stagnant_rounds = 0
            previous_count = len(refs)

            if len(refs) >= limit:
                break

            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(2000)

        if not refs:
            _log_search_diagnostics(page, query, url)
            if debug:
                from radar.upwork.session import DEFAULT_SESSION_DIR

                debug_dir = DEFAULT_SESSION_DIR
                debug_dir.mkdir(parents=True, exist_ok=True)
                screenshot_path = debug_dir / "upwork-search-debug.png"
                html_path = debug_dir / "upwork-search-debug.html"
                page.screenshot(path=str(screenshot_path), full_page=True)
                html_path.write_text(page.content(), encoding="utf-8")
                logger.warning("Saved debug screenshot to %s and HTML to %s", screenshot_path, html_path)

        logger.info("Query %r: found %d jobs", query, len(refs))
        return refs[:limit]
    finally:
        page.close()


def extract_job(context: Any, ref: RawListingRef) -> RawListing:
    page = context.new_page()
    page.set_default_timeout(PAGE_TIMEOUT_MS)
    job_url = ref.url or canonical_job_url(ref.external_id)
    if "/details/" in job_url:
        job_url = canonical_job_url(ref.external_id)

    try:
        page.goto(job_url, wait_until="domcontentloaded")
        page.wait_for_timeout(2000)

        try:
            data = page.evaluate(EXTRACT_JOB_JS)
        except Exception as exc:
            raise ExtractionError(
                f"Failed to extract job {ref.external_id}: {exc}",
                url=job_url,
            ) from exc

        if not isinstance(data, dict):
            raise ExtractionError(f"Unexpected job page data for {ref.external_id}", url=job_url)

        title = (data.get("title") or ref.title or "").strip()
        description = (data.get("description") or "").strip()
        skills = data.get("skills") or []
        features = data.get("features") or []
        page_text = data.get("page_text") or ""
        dom_fields = data.get("dom") if isinstance(data.get("dom"), dict) else {}
        tile_fields = ref.extras.get("tile") if isinstance(ref.extras.get("tile"), dict) else {}

        if not title and not description:
            raise ExtractionError(
                f"Job page returned no content for {ref.external_id}",
                url=job_url,
            )

        extracted = parse_listing_fields(
            title=title,
            description=description,
            skills=skills if isinstance(skills, list) else [],
            features=features if isinstance(features, list) else [],
            page_text=page_text if isinstance(page_text, str) else "",
            dom_fields=dom_fields,
            tile_fields=tile_fields,
            job_id=ref.external_id,
            url=job_url,
            search_query=ref.source_query,
        )
        payload = extracted.model_dump()

        try:
            external_id = parse_job_id_from_url(job_url)
        except ValueError:
            external_id = ref.external_id

        return RawListing(
            platform="upwork",
            external_id=external_id,
            url=job_url,
            title=title or ref.title,
            description=description,
            payload=payload,
        )
    finally:
        page.close()
