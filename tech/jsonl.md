# JSON Lines (.jsonl)

## What it is

JSON Lines is JSON with one rule added: a file holds one complete JSON value per line, usually an object. It suits data sets, because you can append a record, read a file line by line without loading it all, and diff it line by line.

## Why this repository uses it

The 200 sample questions, each with the page it should cite and whether it should pause, are cases. One per line means a diff shows exactly which question changed.

## Where it appears

| File | What it does with JSON Lines (.jsonl) |
| --- | --- |
| `data/questions.jsonl` | 200 questions: 180 to answer, 20 that must pause |
| `scripts/generate_data.py` | writes it and the help pages from one seed |

## How it works underneath

A `.jsonl` file looks like this: each line is a full JSON object; there is no outer `[ ]` and no commas between lines; blank lines are not records. A reader loops over the lines and calls `json.loads(line)` on each. A writer calls `json.dumps(record)` and writes it followed by a newline. Because each line stands alone, a damaged line spoils only that record, and `git diff` shows exactly which records changed.

## Walkthrough of this repository's use

### `data/questions.jsonl`

Each line: the question, the page and section it should cite (`expected_page`, `expected_anchor`) and `should_pause`. `make evaluate` runs all 200 and compares.

200 lines, one JSON object per line. Keys of the first record: `id`, `question`, `expected_page`, `expected_anchor`, `should_pause`. The first record, pretty-printed:

```json
{
  "id": "q-008",
  "question": "A question about changing an address: the delivery address can change until the?",
  "expected_page": "help-08",
  "expected_anchor": "the-delivery-address-can",
  "should_pause": false
}
```


<!-- extras -->
### The data files in full

Every line of each tracked `.jsonl` file is shown below, so the whole dataset can be read here. Each line is one JSON object (one record).

#### `data/questions.jsonl` (200 records)

The keys of a record: `id`, `question`, `expected_page`, `expected_anchor`, `should_pause`.

```json
{"id": "q-008", "question": "A question about changing an address: the delivery address can change until the?", "expected_page": "help-08", "expected_anchor": "the-delivery-address-can", "should_pause": false}
{"id": "q-160", "question": "A question about payment methods: a declined payment keeps the basket for twenty?", "expected_page": "help-10", "expected_anchor": "a-declined-payment-keeps", "should_pause": false}
{"id": "q-103", "question": "A question about resetting a password: use the reset link on the sign in?", "expected_page": "help-13", "expected_anchor": "use-the-reset-link", "should_pause": false}
{"id": "q-199", "question": "How do I tune a guitar string?", "expected_page": null, "expected_anchor": null, "should_pause": true}
{"id": "q-088", "question": "A question about store hours: email replies arrive within one business?", "expected_page": "help-28", "expected_anchor": "email-replies-arrive-within", "should_pause": false}
{"id": "q-118", "question": "A question about store hours: chat support is open every day from eight to?", "expected_page": "help-28", "expected_anchor": "chat-support-is-open", "should_pause": false}
{"id": "q-174", "question": "A question about loyalty points: points expire after twenty four months?", "expected_page": "help-24", "expected_anchor": "points-expire-after-twenty", "should_pause": false}
{"id": "q-019", "question": "A question about international shipping: the shop ships to the countries listed on the shipping page?", "expected_page": "help-19", "expected_anchor": "the-shop-ships-to", "should_pause": false}
{"id": "q-076", "question": "A question about warranty: normal wear is not covered by the warranty?", "expected_page": "help-16", "expected_anchor": "normal-wear-is-not", "should_pause": false}
{"id": "q-021", "question": "A question about pickup points: choose a pickup point at checkout from?", "expected_page": "help-21", "expected_anchor": "choose-a-pickup-point", "should_pause": false}
{"id": "q-073", "question": "A question about resetting a password: support cannot read or set a password for you?", "expected_page": "help-13", "expected_anchor": "support-cannot-read-or", "should_pause": false}
{"id": "q-014", "question": "A question about deleting an account: account deletion is available under privacy settings?", "expected_page": "help-14", "expected_anchor": "account-deletion-is-available", "should_pause": false}
{"id": "q-078", "question": "A question about stock alerts: alerts expire after ninety days?", "expected_page": "help-18", "expected_anchor": "alerts-expire-after-ninety", "should_pause": false}
{"id": "q-176", "question": "A question about bulk orders: bulk orders ship in consolidated pallets?", "expected_page": "help-26", "expected_anchor": "bulk-orders-ship-in", "should_pause": false}
{"id": "q-051", "question": "A question about pickup points: parcels wait at a pickup point for?", "expected_page": "help-21", "expected_anchor": "parcels-wait-at-a", "should_pause": false}
{"id": "q-084", "question": "A question about loyalty points: points expire after twenty four months?", "expected_page": "help-24", "expected_anchor": "points-expire-after-twenty", "should_pause": false}
{"id": "q-045", "question": "A question about privacy and data: a copy of your data can be requested from?", "expected_page": "help-15", "expected_anchor": "a-copy-of-your", "should_pause": false}
{"id": "q-098", "question": "A question about changing an address: the delivery address can change until the order ships?", "expected_page": "help-08", "expected_anchor": "the-delivery-address-can", "should_pause": false}
{"id": "q-026", "question": "A question about bulk orders: orders above twenty units receive a team?", "expected_page": "help-26", "expected_anchor": "orders-above-twenty-units", "should_pause": false}
{"id": "q-186", "question": "Refund request after the window: the parcel came a hundred days ago.", "expected_page": null, "expected_anchor": null, "should_pause": true}
{"id": "q-115", "question": "A question about student discount: students get ten percent off with a verified student?", "expected_page": "help-25", "expected_anchor": "students-get-ten-percent", "should_pause": false}
{"id": "q-183", "question": "Can I get a refund on an order from seventy five days ago?", "expected_page": null, "expected_anchor": null, "should_pause": true}
{"id": "q-040", "question": "A question about payment methods: payment is taken when the order ships?", "expected_page": "help-10", "expected_anchor": "payment-is-taken-when", "should_pause": false}
{"id": "q-080", "question": "A question about express delivery: express delivery is not available on bank holidays?", "expected_page": "help-20", "expected_anchor": "express-delivery-is-not", "should_pause": false}
{"id": "q-082", "question": "A question about customs and duties: returns from abroad use the prepaid?", "expected_page": "help-22", "expected_anchor": "returns-from-abroad-use", "should_pause": false}
{"id": "q-052", "question": "A question about customs and duties: nothing is payable on delivery for prepaid duties?", "expected_page": "help-22", "expected_anchor": "nothing-is-payable-on", "should_pause": false}
{"id": "q-055", "question": "A question about student discount: verification lasts one year?", "expected_page": "help-25", "expected_anchor": "verification-lasts-one-year", "should_pause": false}
{"id": "q-095", "question": "A question about exchanges: an exchange for another size is free within?", "expected_page": "help-05", "expected_anchor": "an-exchange-for-another", "should_pause": false}
{"id": "q-133", "question": "A question about resetting a password: the reset link expires after one?", "expected_page": "help-13", "expected_anchor": "the-reset-link-expires", "should_pause": false}
{"id": "q-043", "question": "A question about resetting a password: the reset link expires after one hour?", "expected_page": "help-13", "expected_anchor": "the-reset-link-expires", "should_pause": false}
{"id": "q-066", "question": "A question about damaged items: damaged parcels can be refused at?", "expected_page": "help-06", "expected_anchor": "damaged-parcels-can-be", "should_pause": false}
{"id": "q-137", "question": "A question about size guide: jackets run true to size while shoes run half a size small?", "expected_page": "help-17", "expected_anchor": "jackets-run-true-to", "should_pause": false}
{"id": "q-130", "question": "A question about payment methods: payment is taken when the?", "expected_page": "help-10", "expected_anchor": "payment-is-taken-when", "should_pause": false}
{"id": "q-131", "question": "A question about promo codes: codes apply to full price items?", "expected_page": "help-11", "expected_anchor": "codes-apply-to-full", "should_pause": false}
{"id": "q-035", "question": "A question about exchanges: the exchange parcel ships once the first item scans at the?", "expected_page": "help-05", "expected_anchor": "the-exchange-parcel-ships", "should_pause": false}
{"id": "q-072", "question": "A question about gift cards: lost gift cards can be blocked and reissued with proof of purchase?", "expected_page": "help-12", "expected_anchor": "lost-gift-cards-can", "should_pause": false}
{"id": "q-128", "question": "A question about changing an address: saved addresses live under account?", "expected_page": "help-08", "expected_anchor": "saved-addresses-live-under", "should_pause": false}
{"id": "q-006", "question": "A question about damaged items: report a damaged item within fourteen days with a?", "expected_page": "help-06", "expected_anchor": "report-a-damaged-item", "should_pause": false}
{"id": "q-121", "question": "A question about shipping times: express delivery arrives within two business days?", "expected_page": "help-01", "expected_anchor": "express-delivery-arrives-within", "should_pause": false}
{"id": "q-127", "question": "A question about missing items: multi item orders can arrive in separate?", "expected_page": "help-07", "expected_anchor": "multi-item-orders-can", "should_pause": false}
{"id": "q-161", "question": "A question about promo codes: expired codes cannot be extended?", "expected_page": "help-11", "expected_anchor": "expired-codes-cannot-be", "should_pause": false}
{"id": "q-027", "question": "A question about gift wrapping: gift wrap is a checkout option for a small?", "expected_page": "help-27", "expected_anchor": "gift-wrap-is-a", "should_pause": false}
{"id": "q-077", "question": "A question about size guide: measurements are given in centimetres and?", "expected_page": "help-17", "expected_anchor": "measurements-are-given-in", "should_pause": false}
{"id": "q-090", "question": "A question about product care: canvas can be machine washed gently?", "expected_page": "help-30", "expected_anchor": "canvas-can-be-machine", "should_pause": false}
{"id": "q-038", "question": "A question about changing an address: saved addresses live under account?", "expected_page": "help-08", "expected_anchor": "saved-addresses-live-under", "should_pause": false}
{"id": "q-063", "question": "A question about return policy: sale items follow the same thirty day?", "expected_page": "help-03", "expected_anchor": "sale-items-follow-the", "should_pause": false}
{"id": "q-091", "question": "A question about shipping times: standard delivery takes three to five business days?", "expected_page": "help-01", "expected_anchor": "standard-delivery-takes-three", "should_pause": false}
{"id": "q-097", "question": "A question about missing items: a missing item should be reported within seven days of delivery?", "expected_page": "help-07", "expected_anchor": "a-missing-item-should", "should_pause": false}
{"id": "q-044", "question": "A question about deleting an account: order history is kept for tax records?", "expected_page": "help-14", "expected_anchor": "order-history-is-kept", "should_pause": false}
{"id": "q-169", "question": "A question about international shipping: delivery abroad takes seven to ten?", "expected_page": "help-19", "expected_anchor": "delivery-abroad-takes-seven", "should_pause": false}
{"id": "q-048", "question": "A question about stock alerts: restock dates are estimates and can move?", "expected_page": "help-18", "expected_anchor": "restock-dates-are-estimates", "should_pause": false}
{"id": "q-124", "question": "A question about refund timing: a refund usually appears on the card within five business?", "expected_page": "help-04", "expected_anchor": "a-refund-usually-appears", "should_pause": false}
{"id": "q-001", "question": "A question about shipping times: standard delivery takes three to five business days after?", "expected_page": "help-01", "expected_anchor": "standard-delivery-takes-three", "should_pause": false}
{"id": "q-141", "question": "A question about pickup points: parcels wait at a pickup point for seven?", "expected_page": "help-21", "expected_anchor": "parcels-wait-at-a", "should_pause": false}
{"id": "q-005", "question": "A question about exchanges: an exchange for another size is free within?", "expected_page": "help-05", "expected_anchor": "an-exchange-for-another", "should_pause": false}
{"id": "q-162", "question": "A question about gift cards: lost gift cards can be blocked and reissued with proof of?", "expected_page": "help-12", "expected_anchor": "lost-gift-cards-can", "should_pause": false}
{"id": "q-111", "question": "A question about pickup points: choose a pickup point at checkout from the map?", "expected_page": "help-21", "expected_anchor": "choose-a-pickup-point", "should_pause": false}
{"id": "q-017", "question": "A question about size guide: every product page links a size guide below the size picker?", "expected_page": "help-17", "expected_anchor": "every-product-page-links", "should_pause": false}
{"id": "q-146", "question": "A question about bulk orders: quotes are valid for fourteen?", "expected_page": "help-26", "expected_anchor": "quotes-are-valid-for", "should_pause": false}
{"id": "q-022", "question": "A question about customs and duties: duties are calculated at checkout for supported countries?", "expected_page": "help-22", "expected_anchor": "duties-are-calculated-at", "should_pause": false}
{"id": "q-092", "question": "A question about tracking a parcel: a tracking link is emailed once the parcel leaves the warehouse?", "expected_page": "help-02", "expected_anchor": "a-tracking-link-is", "should_pause": false}
{"id": "q-023", "question": "A question about invoices and receipts: invoices are attached to each order in?", "expected_page": "help-23", "expected_anchor": "invoices-are-attached-to", "should_pause": false}
{"id": "q-148", "question": "A question about store hours: phone support is closed on bank?", "expected_page": "help-28", "expected_anchor": "phone-support-is-closed", "should_pause": false}
{"id": "q-163", "question": "A question about resetting a password: support cannot read or set a password for you?", "expected_page": "help-13", "expected_anchor": "support-cannot-read-or", "should_pause": false}
{"id": "q-069", "question": "A question about cancelling an order: cancelled gift card payments return to the card balance?", "expected_page": "help-09", "expected_anchor": "cancelled-gift-card-payments", "should_pause": false}
{"id": "q-125", "question": "A question about exchanges: the exchange parcel ships once the first item scans at the?", "expected_page": "help-05", "expected_anchor": "the-exchange-parcel-ships", "should_pause": false}
{"id": "q-013", "question": "A question about resetting a password: use the reset link on the sign in page?", "expected_page": "help-13", "expected_anchor": "use-the-reset-link", "should_pause": false}
{"id": "q-036", "question": "A question about damaged items: a replacement ships at no cost once the photo is?", "expected_page": "help-06", "expected_anchor": "a-replacement-ships-at", "should_pause": false}
{"id": "q-007", "question": "A question about missing items: a missing item should be reported within seven days of delivery?", "expected_page": "help-07", "expected_anchor": "a-missing-item-should", "should_pause": false}
{"id": "q-042", "question": "A question about gift cards: the balance is shown on the gift card page?", "expected_page": "help-12", "expected_anchor": "the-balance-is-shown", "should_pause": false}
{"id": "q-147", "question": "A question about gift wrapping: a printed card carries your?", "expected_page": "help-27", "expected_anchor": "a-printed-card-carries", "should_pause": false}
{"id": "q-192", "question": "What is the capital of Australia?", "expected_page": null, "expected_anchor": null, "should_pause": true}
{"id": "q-056", "question": "A question about bulk orders: quotes are valid for fourteen?", "expected_page": "help-26", "expected_anchor": "quotes-are-valid-for", "should_pause": false}
{"id": "q-058", "question": "A question about store hours: phone support is closed on?", "expected_page": "help-28", "expected_anchor": "phone-support-is-closed", "should_pause": false}
{"id": "q-132", "question": "A question about gift cards: the balance is shown on the gift card?", "expected_page": "help-12", "expected_anchor": "the-balance-is-shown", "should_pause": false}
{"id": "q-135", "question": "A question about privacy and data: a copy of your data can be requested from privacy?", "expected_page": "help-15", "expected_anchor": "a-copy-of-your", "should_pause": false}
{"id": "q-185", "question": "My order arrived eighty days ago, is a refund still possible?", "expected_page": null, "expected_anchor": null, "should_pause": true}
{"id": "q-126", "question": "A question about damaged items: a replacement ships at no cost once the photo?", "expected_page": "help-06", "expected_anchor": "a-replacement-ships-at", "should_pause": false}
{"id": "q-198", "question": "What is the best programming language to learn?", "expected_page": null, "expected_anchor": null, "should_pause": true}
{"id": "q-173", "question": "A question about invoices and receipts: corrected invoices are issued within two?", "expected_page": "help-23", "expected_anchor": "corrected-invoices-are-issued", "should_pause": false}
{"id": "q-139", "question": "A question about international shipping: duties and taxes are shown?", "expected_page": "help-19", "expected_anchor": "duties-and-taxes-are", "should_pause": false}
{"id": "q-086", "question": "A question about bulk orders: bulk orders ship in consolidated pallets?", "expected_page": "help-26", "expected_anchor": "bulk-orders-ship-in", "should_pause": false}
{"id": "q-165", "question": "A question about privacy and data: marketing email can be switched off at any time?", "expected_page": "help-15", "expected_anchor": "marketing-email-can-be", "should_pause": false}
{"id": "q-081", "question": "A question about pickup points: a photo identity document is needed to?", "expected_page": "help-21", "expected_anchor": "a-photo-identity-document", "should_pause": false}
{"id": "q-033", "question": "A question about return policy: returned items must be unused and in the original packaging?", "expected_page": "help-03", "expected_anchor": "returned-items-must-be", "should_pause": false}
{"id": "q-119", "question": "A question about contacting support: use chat for the fastest?", "expected_page": "help-29", "expected_anchor": "use-chat-for-the", "should_pause": false}
{"id": "q-031", "question": "A question about shipping times: express delivery arrives within two business days where available?", "expected_page": "help-01", "expected_anchor": "express-delivery-arrives-within", "should_pause": false}
{"id": "q-107", "question": "A question about size guide: every product page links a size guide below the size picker?", "expected_page": "help-17", "expected_anchor": "every-product-page-links", "should_pause": false}
{"id": "q-184", "question": "I want a refund for something I received fifty days ago.", "expected_page": null, "expected_anchor": null, "should_pause": true}
{"id": "q-105", "question": "A question about privacy and data: personal data is used only to run orders and support?", "expected_page": "help-15", "expected_anchor": "personal-data-is-used", "should_pause": false}
{"id": "q-039", "question": "A question about cancelling an order: a cancelled order releases the payment within three?", "expected_page": "help-09", "expected_anchor": "a-cancelled-order-releases", "should_pause": false}
{"id": "q-175", "question": "A question about student discount: the discount cannot be combined with promo codes?", "expected_page": "help-25", "expected_anchor": "the-discount-cannot-be", "should_pause": false}
{"id": "q-159", "question": "A question about cancelling an order: cancelled gift card payments return to the?", "expected_page": "help-09", "expected_anchor": "cancelled-gift-card-payments", "should_pause": false}
{"id": "q-120", "question": "A question about product care: wool items are hand washed cold?", "expected_page": "help-30", "expected_anchor": "wool-items-are-hand", "should_pause": false}
{"id": "q-030", "question": "A question about product care: wool items are hand washed cold?", "expected_page": "help-30", "expected_anchor": "wool-items-are-hand", "should_pause": false}
{"id": "q-113", "question": "A question about invoices and receipts: invoices are attached to each order in?", "expected_page": "help-23", "expected_anchor": "invoices-are-attached-to", "should_pause": false}
{"id": "q-100", "question": "A question about payment methods: cards, bank transfer and store credit are?", "expected_page": "help-10", "expected_anchor": "cards-bank-transfer-and", "should_pause": false}
{"id": "q-011", "question": "A question about promo codes: each promo code works once per account?", "expected_page": "help-11", "expected_anchor": "each-promo-code-works", "should_pause": false}
{"id": "q-114", "question": "A question about loyalty points: one point is earned for every currency unit spent?", "expected_page": "help-24", "expected_anchor": "one-point-is-earned", "should_pause": false}
{"id": "q-153", "question": "A question about return policy: sale items follow the same thirty day return?", "expected_page": "help-03", "expected_anchor": "sale-items-follow-the", "should_pause": false}
{"id": "q-018", "question": "A question about stock alerts: use notify me on a sold out product to get an email on restock?", "expected_page": "help-18", "expected_anchor": "use-notify-me-on", "should_pause": false}
{"id": "q-060", "question": "A question about product care: leather bags are wiped with a?", "expected_page": "help-30", "expected_anchor": "leather-bags-are-wiped", "should_pause": false}
{"id": "q-053", "question": "A question about invoices and receipts: a company name can be added before the order?", "expected_page": "help-23", "expected_anchor": "a-company-name-can", "should_pause": false}
{"id": "q-096", "question": "A question about damaged items: report a damaged item within fourteen days with?", "expected_page": "help-06", "expected_anchor": "report-a-damaged-item", "should_pause": false}
{"id": "q-182", "question": "It was delivered ninety days ago and I want a refund now.", "expected_page": null, "expected_anchor": null, "should_pause": true}
{"id": "q-143", "question": "A question about invoices and receipts: a company name can be added before the order ships?", "expected_page": "help-23", "expected_anchor": "a-company-name-can", "should_pause": false}
{"id": "q-083", "question": "A question about invoices and receipts: corrected invoices are issued within two business?", "expected_page": "help-23", "expected_anchor": "corrected-invoices-are-issued", "should_pause": false}
{"id": "q-109", "question": "A question about international shipping: the shop ships to the countries listed on the shipping page?", "expected_page": "help-19", "expected_anchor": "the-shop-ships-to", "should_pause": false}
{"id": "q-003", "question": "A question about return policy: items can be returned within thirty days of delivery?", "expected_page": "help-03", "expected_anchor": "items-can-be-returned", "should_pause": false}
{"id": "q-181", "question": "I bought this sixty days ago, can I still get a refund?", "expected_page": null, "expected_anchor": null, "should_pause": true}
{"id": "q-004", "question": "A question about refund timing: refunds are issued to the original payment method after the parcel?", "expected_page": "help-04", "expected_anchor": "refunds-are-issued-to", "should_pause": false}
{"id": "q-154", "question": "A question about refund timing: store credit refunds are available?", "expected_page": "help-04", "expected_anchor": "store-credit-refunds-are", "should_pause": false}
{"id": "q-152", "question": "A question about tracking a parcel: a parcel marked delivered but not received should be reported within five?", "expected_page": "help-02", "expected_anchor": "a-parcel-marked-delivered", "should_pause": false}
{"id": "q-075", "question": "A question about privacy and data: marketing email can be switched off at any time?", "expected_page": "help-15", "expected_anchor": "marketing-email-can-be", "should_pause": false}
{"id": "q-164", "question": "A question about deleting an account: deletion finishes within thirty days?", "expected_page": "help-14", "expected_anchor": "deletion-finishes-within-thirty", "should_pause": false}
{"id": "q-140", "question": "A question about express delivery: express orders must be placed before noon?", "expected_page": "help-20", "expected_anchor": "express-orders-must-be", "should_pause": false}
{"id": "q-187", "question": "I received it forty five days ago and would like my money back, a refund please.", "expected_page": null, "expected_anchor": null, "should_pause": true}
{"id": "q-101", "question": "A question about promo codes: each promo code works once?", "expected_page": "help-11", "expected_anchor": "each-promo-code-works", "should_pause": false}
{"id": "q-117", "question": "A question about gift wrapping: gift wrap is a checkout option for a small fee?", "expected_page": "help-27", "expected_anchor": "gift-wrap-is-a", "should_pause": false}
{"id": "q-129", "question": "A question about cancelling an order: a cancelled order releases the payment within three business?", "expected_page": "help-09", "expected_anchor": "a-cancelled-order-releases", "should_pause": false}
{"id": "q-150", "question": "A question about product care: leather bags are wiped with a damp?", "expected_page": "help-30", "expected_anchor": "leather-bags-are-wiped", "should_pause": false}
{"id": "q-166", "question": "A question about warranty: normal wear is not covered by?", "expected_page": "help-16", "expected_anchor": "normal-wear-is-not", "should_pause": false}
{"id": "q-024", "question": "A question about loyalty points: one point is earned for every currency?", "expected_page": "help-24", "expected_anchor": "one-point-is-earned", "should_pause": false}
{"id": "q-172", "question": "A question about customs and duties: returns from abroad use the prepaid label?", "expected_page": "help-22", "expected_anchor": "returns-from-abroad-use", "should_pause": false}
{"id": "q-046", "question": "A question about warranty: warranty claims need the order number and?", "expected_page": "help-16", "expected_anchor": "warranty-claims-need-the", "should_pause": false}
{"id": "q-178", "question": "A question about store hours: email replies arrive within one business?", "expected_page": "help-28", "expected_anchor": "email-replies-arrive-within", "should_pause": false}
{"id": "q-070", "question": "A question about payment methods: a declined payment keeps the basket for twenty four?", "expected_page": "help-10", "expected_anchor": "a-declined-payment-keeps", "should_pause": false}
{"id": "q-196", "question": "Which planet is closest to the sun?", "expected_page": null, "expected_anchor": null, "should_pause": true}
{"id": "q-123", "question": "A question about return policy: returned items must be unused and in the original?", "expected_page": "help-03", "expected_anchor": "returned-items-must-be", "should_pause": false}
{"id": "q-106", "question": "A question about warranty: products carry a one year warranty against defects?", "expected_page": "help-16", "expected_anchor": "products-carry-a-one", "should_pause": false}
{"id": "q-085", "question": "A question about student discount: the discount cannot be combined with promo?", "expected_page": "help-25", "expected_anchor": "the-discount-cannot-be", "should_pause": false}
{"id": "q-194", "question": "How tall is the tallest mountain in the world?", "expected_page": null, "expected_anchor": null, "should_pause": true}
{"id": "q-010", "question": "A question about payment methods: cards, bank transfer and store credit are accepted?", "expected_page": "help-10", "expected_anchor": "cards-bank-transfer-and", "should_pause": false}
{"id": "q-062", "question": "A question about tracking a parcel: a parcel marked delivered but not received should be reported within five?", "expected_page": "help-02", "expected_anchor": "a-parcel-marked-delivered", "should_pause": false}
{"id": "q-112", "question": "A question about customs and duties: duties are calculated at checkout for?", "expected_page": "help-22", "expected_anchor": "duties-are-calculated-at", "should_pause": false}
{"id": "q-002", "question": "A question about tracking a parcel: a tracking link is emailed once the parcel leaves the?", "expected_page": "help-02", "expected_anchor": "a-tracking-link-is", "should_pause": false}
{"id": "q-015", "question": "A question about privacy and data: personal data is used only to run orders?", "expected_page": "help-15", "expected_anchor": "personal-data-is-used", "should_pause": false}
{"id": "q-156", "question": "A question about damaged items: damaged parcels can be refused at?", "expected_page": "help-06", "expected_anchor": "damaged-parcels-can-be", "should_pause": false}
{"id": "q-151", "question": "A question about shipping times: orders placed after the cutoff hour ship on the next business day?", "expected_page": "help-01", "expected_anchor": "orders-placed-after-the", "should_pause": false}
{"id": "q-087", "question": "A question about gift wrapping: gift wrapped items are packed with no?", "expected_page": "help-27", "expected_anchor": "gift-wrapped-items-are", "should_pause": false}
{"id": "q-032", "question": "A question about tracking a parcel: the tracking page shows the carrier hub the parcel last passed?", "expected_page": "help-02", "expected_anchor": "the-tracking-page-shows", "should_pause": false}
{"id": "q-171", "question": "A question about pickup points: a photo identity document is needed to?", "expected_page": "help-21", "expected_anchor": "a-photo-identity-document", "should_pause": false}
{"id": "q-047", "question": "A question about size guide: jackets run true to size while shoes run half a size small?", "expected_page": "help-17", "expected_anchor": "jackets-run-true-to", "should_pause": false}
{"id": "q-179", "question": "A question about contacting support: escalations are answered by a senior agent within?", "expected_page": "help-29", "expected_anchor": "escalations-are-answered-by", "should_pause": false}
{"id": "q-197", "question": "Can you help me write a poem about autumn?", "expected_page": null, "expected_anchor": null, "should_pause": true}
{"id": "q-188", "question": "Please refund the order I got sixty five days ago.", "expected_page": null, "expected_anchor": null, "should_pause": true}
{"id": "q-064", "question": "A question about refund timing: store credit refunds are available immediately?", "expected_page": "help-04", "expected_anchor": "store-credit-refunds-are", "should_pause": false}
{"id": "q-041", "question": "A question about promo codes: codes apply to full price?", "expected_page": "help-11", "expected_anchor": "codes-apply-to-full", "should_pause": false}
{"id": "q-102", "question": "A question about gift cards: gift cards never expire and can be used across several orders?", "expected_page": "help-12", "expected_anchor": "gift-cards-never-expire", "should_pause": false}
{"id": "q-094", "question": "A question about refund timing: refunds are issued to the original payment method after the parcel?", "expected_page": "help-04", "expected_anchor": "refunds-are-issued-to", "should_pause": false}
{"id": "q-136", "question": "A question about warranty: warranty claims need the order number and?", "expected_page": "help-16", "expected_anchor": "warranty-claims-need-the", "should_pause": false}
{"id": "q-089", "question": "A question about contacting support: escalations are answered by a senior agent within?", "expected_page": "help-29", "expected_anchor": "escalations-are-answered-by", "should_pause": false}
{"id": "q-037", "question": "A question about missing items: multi item orders can arrive in separate boxes?", "expected_page": "help-07", "expected_anchor": "multi-item-orders-can", "should_pause": false}
{"id": "q-193", "question": "Can you recommend a good pasta recipe?", "expected_page": null, "expected_anchor": null, "should_pause": true}
{"id": "q-029", "question": "A question about contacting support: use chat for the fastest?", "expected_page": "help-29", "expected_anchor": "use-chat-for-the", "should_pause": false}
{"id": "q-016", "question": "A question about warranty: products carry a one year warranty?", "expected_page": "help-16", "expected_anchor": "products-carry-a-one", "should_pause": false}
{"id": "q-145", "question": "A question about student discount: verification lasts one year?", "expected_page": "help-25", "expected_anchor": "verification-lasts-one-year", "should_pause": false}
{"id": "q-168", "question": "A question about stock alerts: alerts expire after ninety days?", "expected_page": "help-18", "expected_anchor": "alerts-expire-after-ninety", "should_pause": false}
{"id": "q-061", "question": "A question about shipping times: orders placed after the cutoff hour ship on the next?", "expected_page": "help-01", "expected_anchor": "orders-placed-after-the", "should_pause": false}
{"id": "q-028", "question": "A question about store hours: chat support is open every day from eight to?", "expected_page": "help-28", "expected_anchor": "chat-support-is-open", "should_pause": false}
{"id": "q-195", "question": "What will the weather be like next week?", "expected_page": null, "expected_anchor": null, "should_pause": true}
{"id": "q-170", "question": "A question about express delivery: express delivery is not available on bank holidays?", "expected_page": "help-20", "expected_anchor": "express-delivery-is-not", "should_pause": false}
{"id": "q-190", "question": "Can you refund an order delivered seventy days ago?", "expected_page": null, "expected_anchor": null, "should_pause": true}
{"id": "q-074", "question": "A question about deleting an account: deletion finishes within thirty days?", "expected_page": "help-14", "expected_anchor": "deletion-finishes-within-thirty", "should_pause": false}
{"id": "q-149", "question": "A question about contacting support: include the order number in every?", "expected_page": "help-29", "expected_anchor": "include-the-order-number", "should_pause": false}
{"id": "q-155", "question": "A question about exchanges: colour exchanges depend on current stock?", "expected_page": "help-05", "expected_anchor": "colour-exchanges-depend-on", "should_pause": false}
{"id": "q-191", "question": "Who won the football match yesterday?", "expected_page": null, "expected_anchor": null, "should_pause": true}
{"id": "q-068", "question": "A question about changing an address: a parcel already with the carrier cannot be redirected by?", "expected_page": "help-08", "expected_anchor": "a-parcel-already-with", "should_pause": false}
{"id": "q-158", "question": "A question about changing an address: a parcel already with the carrier cannot be redirected by the?", "expected_page": "help-08", "expected_anchor": "a-parcel-already-with", "should_pause": false}
{"id": "q-200", "question": "When did the first airplane fly?", "expected_page": null, "expected_anchor": null, "should_pause": true}
{"id": "q-034", "question": "A question about refund timing: a refund usually appears on the card within five business days?", "expected_page": "help-04", "expected_anchor": "a-refund-usually-appears", "should_pause": false}
{"id": "q-020", "question": "A question about express delivery: express delivery is offered at checkout when the address qualifies?", "expected_page": "help-20", "expected_anchor": "express-delivery-is-offered", "should_pause": false}
{"id": "q-189", "question": "Is a refund possible for a purchase from ninety five days ago?", "expected_page": null, "expected_anchor": null, "should_pause": true}
{"id": "q-122", "question": "A question about tracking a parcel: the tracking page shows the carrier hub the parcel?", "expected_page": "help-02", "expected_anchor": "the-tracking-page-shows", "should_pause": false}
{"id": "q-093", "question": "A question about return policy: items can be returned within thirty days of delivery?", "expected_page": "help-03", "expected_anchor": "items-can-be-returned", "should_pause": false}
{"id": "q-157", "question": "A question about missing items: the packing slip lists every item that left the?", "expected_page": "help-07", "expected_anchor": "the-packing-slip-lists", "should_pause": false}
{"id": "q-059", "question": "A question about contacting support: include the order number in every?", "expected_page": "help-29", "expected_anchor": "include-the-order-number", "should_pause": false}
{"id": "q-144", "question": "A question about loyalty points: points can be applied at checkout as a discount?", "expected_page": "help-24", "expected_anchor": "points-can-be-applied", "should_pause": false}
{"id": "q-050", "question": "A question about express delivery: express orders must be placed before?", "expected_page": "help-20", "expected_anchor": "express-orders-must-be", "should_pause": false}
{"id": "q-108", "question": "A question about stock alerts: use notify me on a sold out product to get an email on?", "expected_page": "help-18", "expected_anchor": "use-notify-me-on", "should_pause": false}
{"id": "q-142", "question": "A question about customs and duties: nothing is payable on delivery for?", "expected_page": "help-22", "expected_anchor": "nothing-is-payable-on", "should_pause": false}
{"id": "q-009", "question": "A question about cancelling an order: an order can be cancelled until it has been?", "expected_page": "help-09", "expected_anchor": "an-order-can-be", "should_pause": false}
{"id": "q-110", "question": "A question about express delivery: express delivery is offered at checkout when the?", "expected_page": "help-20", "expected_anchor": "express-delivery-is-offered", "should_pause": false}
{"id": "q-134", "question": "A question about deleting an account: order history is kept for tax records?", "expected_page": "help-14", "expected_anchor": "order-history-is-kept", "should_pause": false}
{"id": "q-054", "question": "A question about loyalty points: points can be applied at checkout as a?", "expected_page": "help-24", "expected_anchor": "points-can-be-applied", "should_pause": false}
{"id": "q-104", "question": "A question about deleting an account: account deletion is available under?", "expected_page": "help-14", "expected_anchor": "account-deletion-is-available", "should_pause": false}
{"id": "q-167", "question": "A question about size guide: measurements are given in centimetres?", "expected_page": "help-17", "expected_anchor": "measurements-are-given-in", "should_pause": false}
{"id": "q-065", "question": "A question about exchanges: colour exchanges depend on current stock?", "expected_page": "help-05", "expected_anchor": "colour-exchanges-depend-on", "should_pause": false}
{"id": "q-049", "question": "A question about international shipping: duties and taxes are shown?", "expected_page": "help-19", "expected_anchor": "duties-and-taxes-are", "should_pause": false}
{"id": "q-079", "question": "A question about international shipping: delivery abroad takes seven to ten?", "expected_page": "help-19", "expected_anchor": "delivery-abroad-takes-seven", "should_pause": false}
{"id": "q-067", "question": "A question about missing items: the packing slip lists every item that left the warehouse?", "expected_page": "help-07", "expected_anchor": "the-packing-slip-lists", "should_pause": false}
{"id": "q-071", "question": "A question about promo codes: expired codes cannot be extended by support?", "expected_page": "help-11", "expected_anchor": "expired-codes-cannot-be", "should_pause": false}
{"id": "q-138", "question": "A question about stock alerts: restock dates are estimates and can move?", "expected_page": "help-18", "expected_anchor": "restock-dates-are-estimates", "should_pause": false}
{"id": "q-012", "question": "A question about gift cards: gift cards never expire and can be used across several orders?", "expected_page": "help-12", "expected_anchor": "gift-cards-never-expire", "should_pause": false}
{"id": "q-116", "question": "A question about bulk orders: orders above twenty units receive a?", "expected_page": "help-26", "expected_anchor": "orders-above-twenty-units", "should_pause": false}
{"id": "q-057", "question": "A question about gift wrapping: a printed card carries your?", "expected_page": "help-27", "expected_anchor": "a-printed-card-carries", "should_pause": false}
{"id": "q-180", "question": "A question about product care: canvas can be machine washed gently?", "expected_page": "help-30", "expected_anchor": "canvas-can-be-machine", "should_pause": false}
{"id": "q-099", "question": "A question about cancelling an order: an order can be cancelled until it has?", "expected_page": "help-09", "expected_anchor": "an-order-can-be", "should_pause": false}
{"id": "q-177", "question": "A question about gift wrapping: gift wrapped items are packed with no price slip?", "expected_page": "help-27", "expected_anchor": "gift-wrapped-items-are", "should_pause": false}
{"id": "q-025", "question": "A question about student discount: students get ten percent off with a verified?", "expected_page": "help-25", "expected_anchor": "students-get-ten-percent", "should_pause": false}
```

<!-- /extras -->

## Try it yourself

Run these from the repository folder (after `make up`).

```bash
wc -l data/questions.jsonl
```

`200`.

```bash
python3 -c "import json; rows=[json.loads(l) for l in open('data/questions.jsonl')]; print(sum(r['should_pause'] for r in rows))"
```

`20`.

```bash
make evaluate
```

Prints `paused_of_should: 20`, `paused_of_others: 0` and the citation counts.

## Mistakes people make

- Wrapping the lines in `[ ]` or adding commas; that is plain JSON.
- Pretty-printing a record across several lines; each record must be on one line.
- Forgetting the final newline.
- Loading a huge file at once when streaming line by line would do.
- Letting key order vary, which makes needless diffs. The writers here sort keys.

## Check yourself

1. What is in one line of a `.jsonl` file?
   *Answer:* One complete JSON value, usually an object.
2. Is `[ {...}, {...} ]` valid JSON Lines?
   *Answer:* No; that is one JSON array on one or more lines.
3. How do you read a `.jsonl` file in Python?
   *Answer:* Loop over its lines and call `json.loads` on each.
4. Why is the format good for evaluation cases?
   *Answer:* You can add or remove one case as one line, and a diff shows exactly that.
5. Can records contain nested objects?
   *Answer:* Yes. Only the line structure is special.

## Further reading

- [JSON Lines](https://jsonlines.org/)
- [Python json module](https://docs.python.org/3.12/library/json.html)
