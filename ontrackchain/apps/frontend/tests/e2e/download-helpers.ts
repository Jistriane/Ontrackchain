import { expect, type Page, type Request } from "@playwright/test";

type DownloadLikeResponseOptions = {
  urlPart: string;
  expectedFilename: string;
  method?: "GET" | "POST";
  expectedStatus?: number;
};

export async function expectDownloadLikeResponse(
  page: Page,
  options: DownloadLikeResponseOptions,
  trigger: () => Promise<void>
) {
  const expectedMethod = options.method ?? "GET";
  const expectedStatus = options.expectedStatus ?? 200;

  const responsePromise = page.waitForResponse(
    (response) => response.url().includes(options.urlPart) && response.request().method() === expectedMethod
  );

  await trigger();

  const response = await responsePromise;
  expect(response.status()).toBe(expectedStatus);
  expect((response.headers()["content-disposition"] ?? "").toLowerCase()).toContain(
    options.expectedFilename.toLowerCase()
  );
}

type DownloadWithCapturedRequestOptions<TPayload> = DownloadLikeResponseOptions & {
  requestUrlPart?: string;
  parseRequest: (request: Request) => TPayload;
  assertPayload: (payload: TPayload) => void;
};

export async function expectDownloadLikeResponseWithRequest<TPayload>(
  page: Page,
  options: DownloadWithCapturedRequestOptions<TPayload>,
  trigger: () => Promise<void>
) {
  const expectedMethod = options.method ?? "GET";
  const requestUrlPart = options.requestUrlPart ?? options.urlPart;

  const requestPromise = page.waitForRequest(
    (request) => request.url().includes(requestUrlPart) && request.method() === expectedMethod
  );

  await expectDownloadLikeResponse(page, options, trigger);

  const request = await requestPromise;
  options.assertPayload(options.parseRequest(request));
}
