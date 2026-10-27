"""Write data/help_pages.json (30 pages) and data/questions.jsonl (200 questions with known answers, 20 that should pause).

Deterministic for a seed. Every answerable question is written from the section it should find, so the expected page and
section are known when the question is made.
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOPICS = (
    (
        "Shipping times",
        "delivery",
        [
            "Standard delivery takes three to five business days after dispatch",
            "Express delivery arrives within two business days where available",
            "Orders placed after the cutoff hour ship on the next business day",
        ],
    ),
    (
        "Tracking a parcel",
        "tracking",
        [
            "A tracking link is emailed once the parcel leaves the warehouse",
            "The tracking page shows the carrier hub the parcel last passed",
            "A parcel marked delivered but not received should be reported within five days",
        ],
    ),
    (
        "Return policy",
        "returns",
        [
            "Items can be returned within thirty days of delivery",
            "Returned items must be unused and in the original packaging",
            "Sale items follow the same thirty day return window",
        ],
    ),
    (
        "Refund timing",
        "refunds",
        [
            "Refunds are issued to the original payment method after the parcel is checked",
            "A refund usually appears on the card within five business days",
            "Store credit refunds are available immediately",
        ],
    ),
    (
        "Exchanges",
        "exchange",
        [
            "An exchange for another size is free within thirty days",
            "The exchange parcel ships once the first item scans at the warehouse",
            "Colour exchanges depend on current stock",
        ],
    ),
    (
        "Damaged items",
        "damage",
        [
            "Report a damaged item within fourteen days with a photo",
            "A replacement ships at no cost once the photo is reviewed",
            "Damaged parcels can be refused at the door",
        ],
    ),
    (
        "Missing items",
        "missing",
        [
            "A missing item should be reported within seven days of delivery",
            "Multi item orders can arrive in separate boxes",
            "The packing slip lists every item that left the warehouse",
        ],
    ),
    (
        "Changing an address",
        "address",
        [
            "The delivery address can change until the order ships",
            "Saved addresses live under account settings",
            "A parcel already with the carrier cannot be redirected by the shop",
        ],
    ),
    (
        "Cancelling an order",
        "cancel",
        [
            "An order can be cancelled until it has been dispatched",
            "A cancelled order releases the payment within three business days",
            "Cancelled gift card payments return to the card balance",
        ],
    ),
    (
        "Payment methods",
        "payment",
        [
            "Cards, bank transfer and store credit are accepted",
            "Payment is taken when the order ships",
            "A declined payment keeps the basket for twenty four hours",
        ],
    ),
    (
        "Promo codes",
        "promo",
        [
            "Each promo code works once per account",
            "Codes apply to full price items only",
            "Expired codes cannot be extended by support",
        ],
    ),
    (
        "Gift cards",
        "giftcard",
        [
            "Gift cards never expire and can be used across several orders",
            "The balance is shown on the gift card page",
            "Lost gift cards can be blocked and reissued with proof of purchase",
        ],
    ),
    (
        "Resetting a password",
        "password",
        [
            "Use the reset link on the sign in page",
            "The reset link expires after one hour",
            "Support cannot read or set a password for you",
        ],
    ),
    (
        "Deleting an account",
        "account",
        [
            "Account deletion is available under privacy settings",
            "Order history is kept for tax records after deletion",
            "Deletion finishes within thirty days",
        ],
    ),
    (
        "Privacy and data",
        "privacy",
        [
            "Personal data is used only to run orders and support",
            "A copy of your data can be requested from privacy settings",
            "Marketing email can be switched off at any time",
        ],
    ),
    (
        "Warranty",
        "warranty",
        [
            "Products carry a one year warranty against defects",
            "Warranty claims need the order number and a photo",
            "Normal wear is not covered by the warranty",
        ],
    ),
    (
        "Size guide",
        "sizing",
        [
            "Every product page links a size guide below the size picker",
            "Jackets run true to size while shoes run half a size small",
            "Measurements are given in centimetres and inches",
        ],
    ),
    (
        "Stock alerts",
        "stockalert",
        [
            "Use notify me on a sold out product to get an email on restock",
            "Restock dates are estimates and can move",
            "Alerts expire after ninety days",
        ],
    ),
    (
        "International shipping",
        "abroad",
        [
            "The shop ships to the countries listed on the shipping page",
            "Duties and taxes are shown before payment",
            "Delivery abroad takes seven to ten business days",
        ],
    ),
    (
        "Express delivery",
        "express",
        [
            "Express delivery is offered at checkout when the address qualifies",
            "Express orders must be placed before noon",
            "Express delivery is not available on bank holidays",
        ],
    ),
    (
        "Pickup points",
        "pickup",
        [
            "Choose a pickup point at checkout from the map",
            "Parcels wait at a pickup point for seven days",
            "A photo identity document is needed to collect",
        ],
    ),
    (
        "Customs and duties",
        "customs",
        [
            "Duties are calculated at checkout for supported countries",
            "Nothing is payable on delivery for prepaid duties",
            "Returns from abroad use the prepaid label",
        ],
    ),
    (
        "Invoices and receipts",
        "invoice",
        [
            "Invoices are attached to each order in your account",
            "A company name can be added before the order ships",
            "Corrected invoices are issued within two business days",
        ],
    ),
    (
        "Loyalty points",
        "loyalty",
        [
            "One point is earned for every currency unit spent",
            "Points can be applied at checkout as a discount",
            "Points expire after twenty four months",
        ],
    ),
    (
        "Student discount",
        "student",
        [
            "Students get ten percent off with a verified student email",
            "Verification lasts one year",
            "The discount cannot be combined with promo codes",
        ],
    ),
    (
        "Bulk orders",
        "bulk",
        [
            "Orders above twenty units receive a team quote",
            "Quotes are valid for fourteen days",
            "Bulk orders ship in consolidated pallets",
        ],
    ),
    (
        "Gift wrapping",
        "giftwrap",
        [
            "Gift wrap is a checkout option for a small fee",
            "A printed card carries your message",
            "Gift wrapped items are packed with no price slip",
        ],
    ),
    (
        "Store hours",
        "hours",
        [
            "Chat support is open every day from eight to eight",
            "Phone support is closed on bank holidays",
            "Email replies arrive within one business day",
        ],
    ),
    (
        "Contacting support",
        "contact",
        [
            "Use chat for the fastest answer",
            "Include the order number in every message",
            "Escalations are answered by a senior agent within one day",
        ],
    ),
    (
        "Product care",
        "care",
        [
            "Wool items are hand washed cold",
            "Leather bags are wiped with a damp cloth",
            "Canvas can be machine washed gently",
        ],
    ),
)
UNCOVERED = (
    "Who won the football match yesterday",
    "What is the capital of Australia",
    "Can you recommend a good pasta recipe",
    "How tall is the tallest mountain in the world",
    "What will the weather be like next week",
    "Which planet is closest to the sun",
    "Can you help me write a poem about autumn",
    "What is the best programming language to learn",
    "How do I tune a guitar string",
    "When did the first airplane fly",
)
REFUND_LATE = (
    "I bought this sixty days ago, can I still get a refund?",
    "It was delivered ninety days ago and I want a refund now.",
    "Can I get a refund on an order from seventy five days ago?",
    "I want a refund for something I received fifty days ago.",
    "My order arrived eighty days ago, is a refund still possible?",
    "Refund request after the window: the parcel came a hundred days ago.",
    "I received it forty five days ago and would like my money back, a refund please.",
    "Please refund the order I got sixty five days ago.",
    "Is a refund possible for a purchase from ninety five days ago?",
    "Can you refund an order delivered seventy days ago?",
)


def anchor(heading: str) -> str:
    """URL anchor of a heading."""
    return "-".join(heading.lower().replace(",", "").split()[:4])


def build_pages() -> list[dict[str, object]]:
    """Thirty pages of three sections each."""
    pages = []
    for number, (title, keyword, sentences) in enumerate(TOPICS, start=1):
        sections = []
        for sentence in sentences:
            heading = " ".join(sentence.split()[:5])
            body = f"{sentence}. This applies to {keyword} questions about orders from the shop and is explained in the {title.lower()} page."
            sections.append({"anchor": anchor(heading), "heading": heading, "text": body})
        pages.append({"page_id": f"help-{number:02d}", "title": title, "sections": sections})
    return pages


def build_questions(pages: list[dict[str, object]], rng: random.Random) -> list[dict[str, object]]:
    """180 answerable questions written from a section's own words, 20 that should pause."""
    questions = []
    for index in range(180):
        page = pages[index % len(pages)]
        section = page["sections"][(index // len(pages)) % 3]  # type: ignore[index]
        words = str(section["text"]).split(". ")[0].lower().split()
        keep = words[: max(5, len(words) - rng.randint(0, 2))]
        questions.append(
            {
                "id": f"q-{index + 1:03d}",
                "question": f"A question about {str(page['title']).lower()}: {' '.join(keep)}?",
                "expected_page": page["page_id"],
                "expected_anchor": section["anchor"],
                "should_pause": False,
            }
        )
    for index, text in enumerate(REFUND_LATE):
        questions.append(
            {
                "id": f"q-{181 + index:03d}",
                "question": text,
                "expected_page": None,
                "expected_anchor": None,
                "should_pause": True,
            }
        )
    for index, text in enumerate(UNCOVERED):
        questions.append(
            {
                "id": f"q-{191 + index:03d}",
                "question": f"{text}?",
                "expected_page": None,
                "expected_anchor": None,
                "should_pause": True,
            }
        )
    rng.shuffle(questions)
    return questions


def main() -> int:
    """Write both files."""
    rng = random.Random(int(sys.argv[1]) if len(sys.argv) > 1 else 2610)
    pages = build_pages()
    (ROOT / "data").mkdir(exist_ok=True)
    (ROOT / "data/help_pages.json").write_text(json.dumps(pages, indent=1) + "\n", encoding="utf-8")
    questions = build_questions(pages, rng)
    (ROOT / "data/questions.jsonl").write_text("".join(json.dumps(q) + "\n" for q in questions), encoding="utf-8")
    print(
        f"wrote data/help_pages.json ({len(pages)} pages) and data/questions.jsonl ({len(questions)} questions, {sum(q['should_pause'] for q in questions)} should pause)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
