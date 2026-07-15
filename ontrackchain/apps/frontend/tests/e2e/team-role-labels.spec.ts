import { expect, test, type Page, type Route } from "@playwright/test";

type ExternalIdentityMutationPayload = {
  provider?: string;
  external_subject?: string;
  email_snapshot?: string;
  role_snapshot?: string;
};

type FederatedSuggestionPayload = {
  member_id?: string;
  provider?: string;
  external_subject?: string;
};

function isJsonObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function readOptionalString(value: unknown) {
  return typeof value === "string" ? value : undefined;
}

function parseExternalIdentityMutationPayload(route: Route): ExternalIdentityMutationPayload {
  const payload = JSON.parse(route.request().postData() ?? "{}") as unknown;
  if (!isJsonObject(payload)) {
    return {};
  }

  return {
    provider: readOptionalString(payload.provider),
    external_subject: readOptionalString(payload.external_subject),
    email_snapshot: readOptionalString(payload.email_snapshot),
    role_snapshot: readOptionalString(payload.role_snapshot)
  };
}

function parseFederatedSuggestionPayload(route: Route): FederatedSuggestionPayload {
  const payload = JSON.parse(route.request().postData() ?? "{}") as unknown;
  if (!isJsonObject(payload)) {
    return {};
  }

  return {
    member_id: readOptionalString(payload.member_id),
    provider: readOptionalString(payload.provider),
    external_subject: readOptionalString(payload.external_subject)
  };
}

async function seedFrontendAuth(page: Page) {
  await page.context().addCookies([
    {
      name: "otc_token",
      value: "pw-e2e-token",
      domain: "localhost",
      path: "/",
      httpOnly: false,
      secure: false,
      sameSite: "Lax"
    }
  ]);

  await page.route("**/api/app/auth/context", async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        org_id: "org-e2e",
        user_id: "user-e2e",
        linked_user_id: "linked-e2e",
        role: "ADMIN",
        plan: "professional",
        auth_method: "jwt",
        mfa_mode: "totp",
        mfa_provider_homologated: "true"
      })
    });
  });

  await page.route("**/api/app/team/users", async (route: Route) => {
    if (route.request().method() === "GET") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ data: [] })
      });
      return;
    }

    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        member_id: "team-member-e2e-01",
        name: "compliance@ontrackchain.local",
        email: "compliance@ontrackchain.local",
        role: "COMPLIANCE_OFFICER",
        status: "invited",
        note: "",
        linked_identity_count: 1,
        last_identity_seen_at: "2026-07-06T12:09:00.000Z",
        created_at: "2026-07-06T12:00:00.000Z",
        updated_at: "2026-07-06T12:10:00.000Z"
      })
    });
  });
}

test.describe("team role labels", () => {
  test("renderiza roles com label amigavel e permite busca pelo label traduzido", async ({ page }) => {
    await seedFrontendAuth(page);
    await page.goto("/team");

    await expect(page.locator('[data-testid="team-role-select"] option[value="COMPLIANCE_OFFICER"]')).toHaveText(
      "Oficial de Compliance (COMPLIANCE_OFFICER)"
    );

    await page.getByRole("textbox", { name: "Email", exact: true }).fill("compliance@ontrackchain.local");
    await page.locator('[data-testid="team-role-select"]').selectOption("COMPLIANCE_OFFICER");
    await page.getByRole("button", { name: "Adicionar" }).click();

    const row = page.locator('[data-testid="team-row"]').first();
    await expect(row).toContainText("Oficial de Compliance (COMPLIANCE_OFFICER)");
    await expect(row.getByTestId("team-row-status")).toContainText("convidado");
    await expect(row.getByTestId("team-row-identity")).toContainText("vinculada");
    await expect(row.getByTestId("team-row-identity")).toContainText("Última vista:");
    await expect(row.getByTestId("team-row-updated")).not.toContainText(/T\d{2}:\d{2}:\d{2}\.\d{3}Z/);

    await page.locator('[data-testid="team-search-input"]').fill("oficial");
    await expect(page.locator('[data-testid="team-row"]')).toHaveCount(1);
    await expect(page.locator('[data-testid="team-row"]').first()).toContainText("compliance@ontrackchain.local");
  });

  test("exibe os novos papeis canonicos incrementais no seletor", async ({ page }) => {
    await seedFrontendAuth(page);
    await page.goto("/team");

    await expect(page.locator('[data-testid="team-role-select"] option[value="REVIEWER"]')).toHaveText("Revisor (REVIEWER)");
    await expect(page.locator('[data-testid="team-role-select"] option[value="BILLING_ADMIN"]')).toHaveText(
      "Administrador de Billing (BILLING_ADMIN)"
    );
  });

  test("oculta vínculo manual e desvinculação para role sem permissão administrativa de diretório", async ({ page }) => {
    await page.context().addCookies([
      {
        name: "otc_token",
        value: "pw-e2e-token",
        domain: "localhost",
        path: "/",
        httpOnly: false,
        secure: false,
        sameSite: "Lax"
      }
    ]);

    await page.route("**/api/app/auth/context", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          org_id: "org-e2e",
          user_id: "user-e2e",
          linked_user_id: "linked-e2e",
          role: "VIEWER",
          plan: "professional",
          auth_method: "jwt",
          mfa_mode: "totp",
          mfa_provider_homologated: "true"
        })
      });
    });

    await page.route("**/api/app/team/users", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: [
            {
              member_id: "team-member-e2e-viewer-01",
              name: "viewer@ontrackchain.local",
              email: "viewer@ontrackchain.local",
              role: "VIEWER",
              status: "active",
              note: "",
              linked_identity_count: 1,
              last_identity_seen_at: "2026-07-06T12:13:00.000Z",
              created_at: "2026-07-06T12:00:00.000Z",
              updated_at: "2026-07-06T12:10:00.000Z"
            }
          ]
        })
      });
    });

    await page.goto("/team");
    await page.getByRole("button", { name: "Editar" }).click();

    await expect(page.getByTestId("team-identity-manual-link-restricted")).toContainText(
      "O vínculo manual de identidade federada está oculto nesta sessão"
    );
    await expect(page.getByTestId("team-link-identity-button")).toHaveCount(0);
    await expect(page.getByTestId("team-identity-unlink-button")).toHaveCount(0);
    await expect(page.getByText("Os detalhes completos e a desvinculação manual ficam restritos a administradores do tenant.")).toBeVisible();
    await expect(page.getByTestId("team-federated-search-button")).toBeDisabled();
  });

  test("humaniza a negação tardia da busca assistida quando o backend recusa o diretório federado", async ({ page }) => {
    await seedFrontendAuth(page);

    await page.route("**/api/app/team/users", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: [
            {
              member_id: "team-member-e2e-search-01",
              name: "admin@ontrackchain.local",
              email: "admin@ontrackchain.local",
              role: "ADMIN",
              status: "active",
              note: "",
              linked_identity_count: 0,
              last_identity_seen_at: null,
              created_at: "2026-07-06T12:00:00.000Z",
              updated_at: "2026-07-06T12:10:00.000Z"
            }
          ]
        })
      });
    });

    await page.route("**/api/app/team/users/team-member-e2e-search-01/external-identities", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ data: [] })
      });
    });

    await page.route("**/api/app/team/federated-directory/users?**", async (route: Route) => {
      await route.fulfill({
        status: 403,
        contentType: "application/json",
        body: JSON.stringify({ detail: "team_federated_directory_search_role_required" })
      });
    });

    await page.goto("/team");
    await page.getByRole("button", { name: "Editar" }).click();
    await page.getByTestId("team-federated-search-input").fill("admin");
    await page.getByTestId("team-federated-search-button").click();

    await expect(
      page.getByText("A busca assistida no diretório federado exige papel administrativo de diretório: ADMIN.")
    ).toBeVisible();
    await expect(page.getByText("team_federated_directory_search_role_required")).toHaveCount(0);
  });

  test("humaniza a negação tardia da validação assistida quando o backend recusa a sugestão federada", async ({ page }) => {
    await seedFrontendAuth(page);

    await page.route("**/api/app/team/users", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: [
            {
              member_id: "team-member-e2e-suggestion-01",
              name: "admin@ontrackchain.local",
              email: "admin@ontrackchain.local",
              role: "ADMIN",
              status: "active",
              note: "",
              linked_identity_count: 0,
              last_identity_seen_at: null,
              created_at: "2026-07-06T12:00:00.000Z",
              updated_at: "2026-07-06T12:10:00.000Z"
            }
          ]
        })
      });
    });

    await page.route("**/api/app/team/users/team-member-e2e-suggestion-01/external-identities", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ data: [] })
      });
    });

    await page.route("**/api/app/team/federated-directory/users?**", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: [
            {
              provider: "keycloak",
              external_subject: "kc-sub-admin-01",
              email: "admin@ontrackchain.local",
              username: "admin",
              organization_id: "org-e2e",
              role_snapshot: "ADMIN",
              enabled: true,
              match_status: "suggested",
              linked_user_id: null,
              linked_user_email: null,
              role_validation_status: "valid",
              warnings: []
            }
          ]
        })
      });
    });

    await page.route("**/api/app/team/federated-directory/suggestions", async (route: Route) => {
      const payload = parseFederatedSuggestionPayload(route);

      expect(payload.member_id).toBe("team-member-e2e-suggestion-01");
      expect(payload.provider).toBe("keycloak");
      expect(payload.external_subject).toBe("kc-sub-admin-01");

      await route.fulfill({
        status: 403,
        contentType: "application/json",
        body: JSON.stringify({ detail: "team_federated_directory_suggestion_role_required" })
      });
    });

    await page.goto("/team");
    await page.getByRole("button", { name: "Editar" }).click();
    await page.getByTestId("team-federated-search-input").fill("admin");
    await page.getByTestId("team-federated-search-button").click();
    await page.getByTestId("team-federated-link-button").click();

    await expect(
      page.getByText("A validação assistida de sugestão federada exige papel administrativo de diretório: ADMIN.")
    ).toBeVisible();
    await expect(page.getByText("team_federated_directory_suggestion_role_required")).toHaveCount(0);
  });

  test("humaniza a negação tardia da criação de usuário quando o backend recusa a mutação administrativa", async ({ page }) => {
    await seedFrontendAuth(page);

    await page.route("**/api/app/team/users", async (route: Route) => {
      if (route.request().method() === "GET") {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({ data: [] })
        });
        return;
      }

      await route.fulfill({
        status: 403,
        contentType: "application/json",
        body: JSON.stringify({ detail: "team_user_create_role_required" })
      });
    });

    await page.goto("/team");
    await page.getByRole("textbox", { name: "Email", exact: true }).fill("admin2@ontrackchain.local");
    await page.getByRole("button", { name: "Adicionar" }).click();

    await expect(page.getByText("A criação de usuário no diretório do tenant exige papel administrativo: ADMIN.")).toBeVisible();
    await expect(page.getByText("team_user_create_role_required")).toHaveCount(0);
  });

  test("humaniza a negação tardia da edição de usuário quando o backend recusa a mutação administrativa", async ({ page }) => {
    await seedFrontendAuth(page);

    await page.route("**/api/app/team/users", async (route: Route) => {
      if (route.request().method() === "GET") {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            data: [
              {
                member_id: "team-member-e2e-update-01",
                name: "analyst@ontrackchain.local",
                email: "analyst@ontrackchain.local",
                role: "ANALYST",
                status: "active",
                note: "",
                linked_identity_count: 0,
                last_identity_seen_at: null,
                created_at: "2026-07-06T12:00:00.000Z",
                updated_at: "2026-07-06T12:10:00.000Z"
              }
            ]
          })
        });
        return;
      }

    });

    await page.route("**/api/app/team/users/team-member-e2e-update-01", async (route: Route) => {
      await route.fulfill({
        status: 403,
        contentType: "application/json",
        body: JSON.stringify({ detail: "team_user_update_role_required" })
      });
    });

    await page.goto("/team");
    await page.getByRole("button", { name: "Editar" }).click();
    await page.getByRole("textbox", { name: "Nome", exact: true }).fill("analyst-updated");
    await page.getByRole("button", { name: "Salvar" }).click();

    await expect(page.getByText("A edição de usuário no diretório do tenant exige papel administrativo: ADMIN.")).toBeVisible();
    await expect(page.getByText("team_user_update_role_required")).toHaveCount(0);
  });

  test("humaniza a negação tardia da desativação de usuário quando o backend recusa a mutação administrativa", async ({ page }) => {
    await seedFrontendAuth(page);

    await page.route("**/api/app/team/users", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: [
            {
              member_id: "team-member-e2e-disable-01",
              name: "reviewer@ontrackchain.local",
              email: "reviewer@ontrackchain.local",
              role: "REVIEWER",
              status: "active",
              note: "",
              linked_identity_count: 0,
              last_identity_seen_at: null,
              created_at: "2026-07-06T12:00:00.000Z",
              updated_at: "2026-07-06T12:10:00.000Z"
            }
          ]
        })
      });
    });

    await page.route("**/api/app/team/users/team-member-e2e-disable-01", async (route: Route) => {
      await route.fulfill({
        status: 403,
        contentType: "application/json",
        body: JSON.stringify({ detail: "team_user_disable_role_required" })
      });
    });

    await page.goto("/team");
    await page.getByRole("button", { name: "Desabilitar" }).click();

    await expect(page.getByText("A desativação de usuário no diretório do tenant exige papel administrativo: ADMIN.")).toBeVisible();
    await expect(page.getByText("team_user_disable_role_required")).toHaveCount(0);
  });

  test("humaniza a negação tardia da leitura detalhada de vínculos federados quando o backend recusa o carregamento", async ({
    page
  }) => {
    await seedFrontendAuth(page);

    await page.route("**/api/app/team/users", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: [
            {
              member_id: "team-member-e2e-read-01",
              name: "admin@ontrackchain.local",
              email: "admin@ontrackchain.local",
              role: "ADMIN",
              status: "active",
              note: "",
              linked_identity_count: 1,
              last_identity_seen_at: "2026-07-06T12:13:00.000Z",
              created_at: "2026-07-06T12:00:00.000Z",
              updated_at: "2026-07-06T12:10:00.000Z"
            }
          ]
        })
      });
    });

    await page.route("**/api/app/team/users/team-member-e2e-read-01/external-identities", async (route: Route) => {
      await route.fulfill({
        status: 403,
        contentType: "application/json",
        body: JSON.stringify({ detail: "team_federated_identity_read_role_required" })
      });
    });

    await page.goto("/team");
    await page.getByRole("button", { name: "Editar" }).click();

    await expect(
      page.getByText("A leitura detalhada de identidades federadas do usuário exige papel administrativo de diretório: ADMIN.")
    ).toBeVisible();
    await expect(page.getByText("team_federated_identity_read_role_required")).toHaveCount(0);
  });

  test("permite vincular manualmente uma identidade federada ao membro selecionado", async ({ page }) => {
    let linkedIdentities: Array<{
      provider: string;
      external_subject: string;
      email_snapshot: string;
      role_snapshot: string;
      created_at: string;
      last_seen_at: string | null;
    }> = [];

    await page.context().addCookies([
      {
        name: "otc_token",
        value: "pw-e2e-token",
        domain: "localhost",
        path: "/",
        httpOnly: false,
        secure: false,
        sameSite: "Lax"
      }
    ]);

    await page.route("**/api/app/auth/context", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          org_id: "org-e2e",
          user_id: "user-e2e",
          linked_user_id: "linked-e2e",
          role: "ADMIN",
          plan: "professional",
          auth_method: "jwt",
          mfa_mode: "totp",
          mfa_provider_homologated: "true"
        })
      });
    });

    await page.route("**/api/app/team/users", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: [
            {
              member_id: "team-member-e2e-02",
              name: "analyst@ontrackchain.local",
              email: "analyst@ontrackchain.local",
              role: "ANALYST",
              status: "active",
              note: "",
              linked_identity_count: 0,
              last_identity_seen_at: null,
              created_at: "2026-07-06T12:00:00.000Z",
              updated_at: "2026-07-06T12:10:00.000Z"
            }
          ]
        })
      });
    });

    await page.route("**/api/app/team/users/team-member-e2e-02/external-identities", async (route: Route) => {
      if (route.request().method() === "GET") {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({ data: linkedIdentities })
        });
        return;
      }

      const payload = parseExternalIdentityMutationPayload(route);

      expect(payload.provider).toBe("keycloak");
      expect(payload.external_subject).toBe("kc-sub-analyst-01");
      expect(payload.email_snapshot).toBe("analyst@ontrackchain.local");
      expect(payload.role_snapshot).toBe("ANALYST");

      linkedIdentities = [
        {
          provider: "keycloak",
          external_subject: "kc-sub-analyst-01",
          email_snapshot: "analyst@ontrackchain.local",
          role_snapshot: "ANALYST",
          created_at: "2026-07-06T12:12:00.000Z",
          last_seen_at: null
        }
      ];

      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          member_id: "team-member-e2e-02",
          name: "analyst@ontrackchain.local",
          email: "analyst@ontrackchain.local",
          role: "ANALYST",
          status: "active",
          note: "",
          linked_identity_count: 1,
          last_identity_seen_at: null,
          created_at: "2026-07-06T12:00:00.000Z",
          updated_at: "2026-07-06T12:10:00.000Z"
        })
      });
    });

    await page.goto("/team");
    await page.getByRole("button", { name: "Editar" }).click();
    await page.getByTestId("team-identity-subject-input").fill("kc-sub-analyst-01");
    await page.getByTestId("team-link-identity-button").click();

    await expect(page.getByText("Identidade federada vinculada ao usuário selecionado.")).toBeVisible();
    await expect(page.locator('[data-testid="team-row"]').first().getByTestId("team-row-identity")).toContainText("vinculada");
    await expect(page.locator('[data-testid="team-identity-linked-item"]')).toHaveCount(1);
    await expect(page.locator('[data-testid="team-identity-linked-item"]').first()).toContainText("kc-sub-analyst-01");
  });

  test("exibe detalhes do vínculo persistido e permite desvincular com confirmação", async ({ page }) => {
    let linkedIdentities = [
      {
        provider: "keycloak",
        external_subject: "kc-sub-analyst-02",
        email_snapshot: "analyst@ontrackchain.local",
        role_snapshot: "ANALYST",
        created_at: "2026-07-06T12:12:00.000Z",
        last_seen_at: "2026-07-06T12:13:00.000Z"
      }
    ];

    await page.context().addCookies([
      {
        name: "otc_token",
        value: "pw-e2e-token",
        domain: "localhost",
        path: "/",
        httpOnly: false,
        secure: false,
        sameSite: "Lax"
      }
    ]);

    await page.route("**/api/app/auth/context", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          org_id: "org-e2e",
          user_id: "user-e2e",
          linked_user_id: "linked-e2e",
          role: "ADMIN",
          plan: "professional",
          auth_method: "jwt",
          mfa_mode: "totp",
          mfa_provider_homologated: "true"
        })
      });
    });

    await page.route("**/api/app/team/users", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: [
            {
              member_id: "team-member-e2e-03",
              name: "analyst@ontrackchain.local",
              email: "analyst@ontrackchain.local",
              role: "ANALYST",
              status: "active",
              note: "",
              linked_identity_count: linkedIdentities.length,
              last_identity_seen_at: linkedIdentities[0]?.last_seen_at ?? null,
              created_at: "2026-07-06T12:00:00.000Z",
              updated_at: "2026-07-06T12:10:00.000Z"
            }
          ]
        })
      });
    });

    await page.route("**/api/app/team/users/team-member-e2e-03/external-identities", async (route: Route) => {
      if (route.request().method() === "GET") {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({ data: linkedIdentities })
        });
        return;
      }

      const payload = parseExternalIdentityMutationPayload(route);
      expect(payload.provider).toBe("keycloak");
      expect(payload.external_subject).toBe("kc-sub-analyst-02");

      linkedIdentities = [];

      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          member_id: "team-member-e2e-03",
          name: "analyst@ontrackchain.local",
          email: "analyst@ontrackchain.local",
          role: "ANALYST",
          status: "active",
          note: "",
          linked_identity_count: 0,
          last_identity_seen_at: null,
          created_at: "2026-07-06T12:00:00.000Z",
          updated_at: "2026-07-06T12:10:00.000Z"
        })
      });
    });

    await page.goto("/team");
    await page.getByRole("button", { name: "Editar" }).click();

    const linkedItem = page.locator('[data-testid="team-identity-linked-item"]').first();
    await expect(linkedItem).toContainText("keycloak");
    await expect(linkedItem).toContainText("kc-sub-analyst-02");
    await expect(linkedItem).toContainText("analyst@ontrackchain.local");

    await page.getByTestId("team-identity-unlink-button").click();
    await expect(page.getByTestId("team-confirm-dialog-unlink-identity")).toBeVisible();
    await expect(page.getByTestId("team-confirm-dialog-unlink-identity")).toContainText("Confirmar desvinculação");
    await page.getByTestId("team-confirm-dialog-unlink-identity-confirm").click();

    await expect(page.getByText("Identidade federada desvinculada do usuário selecionado.")).toBeVisible();
    await expect(page.locator('[data-testid="team-row"]').first().getByTestId("team-row-identity")).toContainText("sem vínculo");
    await expect(page.getByText("Nenhuma identidade federada persistida para o membro selecionado.")).toBeVisible();
  });

  test("expõe deep-links contextuais para o preset de identidade federada no Audit", async ({ page }) => {
    const linkedIdentities = [
      {
        provider: "keycloak",
        external_subject: "kc-sub-analyst-04",
        email_snapshot: "analyst@ontrackchain.local",
        role_snapshot: "ANALYST",
        created_at: "2026-07-06T12:12:00.000Z",
        last_seen_at: "2026-07-06T12:13:00.000Z"
      }
    ];

    await page.context().addCookies([
      {
        name: "otc_token",
        value: "pw-e2e-token",
        domain: "localhost",
        path: "/",
        httpOnly: false,
        secure: false,
        sameSite: "Lax"
      }
    ]);

    await page.route("**/api/app/auth/context", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          org_id: "org-e2e",
          user_id: "user-e2e",
          linked_user_id: "linked-e2e",
          role: "ADMIN",
          plan: "professional",
          auth_method: "jwt",
          mfa_mode: "totp",
          mfa_provider_homologated: "true"
        })
      });
    });

    await page.route("**/api/app/team/users", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: [
            {
              member_id: "team-member-e2e-04",
              name: "analyst@ontrackchain.local",
              email: "analyst@ontrackchain.local",
              role: "ANALYST",
              status: "active",
              note: "",
              linked_identity_count: 1,
              last_identity_seen_at: linkedIdentities[0]?.last_seen_at ?? null,
              created_at: "2026-07-06T12:00:00.000Z",
              updated_at: "2026-07-06T12:10:00.000Z"
            }
          ]
        })
      });
    });

    await page.route("**/api/app/team/users/team-member-e2e-04/external-identities", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ data: linkedIdentities })
      });
    });

    await page.goto("/team");

    const row = page.locator('[data-testid="team-row"]').first();
    await expect(row.getByTestId("team-row-open-audit")).toHaveAttribute(
      "href",
      "/audit?preset=identity-federated&resource_id=team-member-e2e-04"
    );

    await page.getByRole("button", { name: "Editar" }).click();
    await expect(page.getByTestId("team-open-identity-audit-button")).toHaveAttribute(
      "href",
      "/audit?preset=identity-federated&resource_id=team-member-e2e-04"
    );
    await expect(page.getByTestId("team-identity-open-audit-button")).toHaveAttribute(
      "href",
      "/audit?preset=identity-federated&resource_id=team-member-e2e-04"
    );
  });

  test("permite buscar no diretório federado e vincular com validação assistida", async ({ page }) => {
    let linkedIdentities: Array<{
      provider: string;
      external_subject: string;
      email_snapshot: string;
      role_snapshot: string;
      created_at: string;
      last_seen_at: string | null;
    }> = [];

    await seedFrontendAuth(page);

    await page.route("**/api/app/team/users", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: [
            {
              member_id: "team-member-e2e-05",
              name: "analyst@ontrackchain.local",
              email: "analyst@ontrackchain.local",
              role: "ANALYST",
              status: "active",
              note: "",
              linked_identity_count: linkedIdentities.length,
              last_identity_seen_at: linkedIdentities[0]?.last_seen_at ?? null,
              created_at: "2026-07-06T12:00:00.000Z",
              updated_at: "2026-07-06T12:10:00.000Z"
            }
          ]
        })
      });
    });

    await page.route("**/api/app/team/users/team-member-e2e-05/external-identities", async (route: Route) => {
      if (route.request().method() === "GET") {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({ data: linkedIdentities })
        });
        return;
      }

      const payload = parseExternalIdentityMutationPayload(route);
      expect(payload.provider).toBe("keycloak");
      expect(payload.external_subject).toBe("kc-sub-analyst-05");
      expect(payload.email_snapshot).toBe("analyst@ontrackchain.local");
      expect(payload.role_snapshot).toBe("ANALYST");

      linkedIdentities = [
        {
          provider: "keycloak",
          external_subject: "kc-sub-analyst-05",
          email_snapshot: "analyst@ontrackchain.local",
          role_snapshot: "ANALYST",
          created_at: "2026-07-06T12:12:00.000Z",
          last_seen_at: null
        }
      ];

      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          member_id: "team-member-e2e-05",
          name: "analyst@ontrackchain.local",
          email: "analyst@ontrackchain.local",
          role: "ANALYST",
          status: "active",
          note: "",
          linked_identity_count: 1,
          last_identity_seen_at: null,
          created_at: "2026-07-06T12:00:00.000Z",
          updated_at: "2026-07-06T12:10:00.000Z"
        })
      });
    });

    await page.route("**/api/app/team/federated-directory/users?**", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: [
            {
              provider: "keycloak",
              external_subject: "kc-sub-analyst-05",
              email: "analyst@ontrackchain.local",
              username: "analyst",
              organization_id: "org-e2e",
              role_snapshot: "ANALYST",
              enabled: true,
              match_status: "suggested",
              linked_user_id: null,
              linked_user_email: null,
              role_validation_status: "valid",
              warnings: []
            }
          ]
        })
      });
    });

    await page.route("**/api/app/team/federated-directory/suggestions", async (route: Route) => {
      const payload = parseFederatedSuggestionPayload(route);

      expect(payload.member_id).toBe("team-member-e2e-05");
      expect(payload.provider).toBe("keycloak");
      expect(payload.external_subject).toBe("kc-sub-analyst-05");

      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          can_link: true,
          match_reason: "ready",
          org_match: true,
          email_match: true,
          provider: "keycloak",
          external_subject: "kc-sub-analyst-05",
          candidate_email: "analyst@ontrackchain.local",
          candidate_username: "analyst",
          candidate_org: "org-e2e",
          role_snapshot: "ANALYST",
          role_validation_status: "valid",
          linked_user_id: null,
          linked_user_email: null,
          warnings: []
        })
      });
    });

    await page.goto("/team");
    await page.getByRole("button", { name: "Editar" }).click();

    await page.getByTestId("team-federated-search-input").fill("analyst");
    await page.getByTestId("team-federated-search-button").click();

    await expect(page.getByTestId("team-federated-results-table")).toBeVisible();
    await expect(page.locator('[data-testid="team-federated-result-row"]')).toHaveCount(1);
    await expect(page.getByText("kc-sub-analyst-05")).toBeVisible();
    await expect(page.getByTestId("team-federated-summary-total")).toContainText("1");
    await expect(page.getByTestId("team-federated-summary-ready")).toContainText("1");
    await expect(page.getByTestId("team-federated-summary-linked")).toContainText("0");
    await expect(page.getByTestId("team-federated-summary-review")).toContainText("0");

    await page.getByTestId("team-federated-link-button").click();

    await expect(page.getByText("Identidade federada vinculada ao usuário selecionado.")).toBeVisible();
    await expect(page.locator('[data-testid="team-row"]').first().getByTestId("team-row-identity")).toContainText("vinculada");
  });

  test("humaniza match status, validação de role e warnings do diretório federado", async ({ page }) => {
    await seedFrontendAuth(page);

    await page.route("**/api/app/team/users", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: [
            {
              member_id: "team-member-e2e-06",
              name: "analyst@ontrackchain.local",
              email: "analyst@ontrackchain.local",
              role: "ANALYST",
              status: "active",
              note: "",
              linked_identity_count: 0,
              last_identity_seen_at: null,
              created_at: "2026-07-06T12:00:00.000Z",
              updated_at: "2026-07-06T12:10:00.000Z"
            }
          ]
        })
      });
    });

    await page.route("**/api/app/team/users/team-member-e2e-06/external-identities", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ data: [] })
      });
    });

    await page.route("**/api/app/team/federated-directory/users?**", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: [
            {
              provider: "keycloak",
              external_subject: "kc-sub-analyst-06",
              email: "risk-analyst@external.local",
              username: "risk-analyst",
              organization_id: "foreign-org",
              role_snapshot: null,
              enabled: true,
              match_status: "org_match_only",
              linked_user_id: null,
              linked_user_email: null,
              role_validation_status: "missing",
              warnings: ["candidate_org_mismatch", "candidate_role_missing", "candidate_email_mismatch"]
            }
          ]
        })
      });
    });

    await page.goto("/team");
    await page.getByRole("button", { name: "Editar" }).click();

    await page.getByTestId("team-federated-search-input").fill("risk");
    await page.getByTestId("team-federated-search-button").click();

    const row = page.locator('[data-testid="team-federated-result-row"]').first();
    await expect(row).toBeVisible();
    await expect(page.getByTestId("team-federated-summary-total")).toContainText("1");
    await expect(page.getByTestId("team-federated-summary-ready")).toContainText("0");
    await expect(page.getByTestId("team-federated-summary-linked")).toContainText("0");
    await expect(page.getByTestId("team-federated-summary-review")).toContainText("1");
    await expect(row.getByTestId("team-federated-match-status")).toContainText("Org compatível, validar email/role");
    await expect(row.getByTestId("team-federated-role-validation")).toContainText("Role ausente no cadastro externo");
    await expect(row).toContainText("Organização externa diverge do tenant selecionado.");
    await expect(row).toContainText("Role ausente no cadastro externo.");
    await expect(row).toContainText("Email externo diverge do membro selecionado.");
    await expect(row.getByTestId("team-federated-link-button")).toBeDisabled();
    await expect(row).not.toContainText("org_match_only");
    await expect(row).not.toContainText("candidate_role_missing");
    await expect(row).not.toContainText("candidate_email_mismatch");
  });

  test("humaniza a rejeição tardia da validação assistida quando o backend recusa o vínculo", async ({ page }) => {
    await seedFrontendAuth(page);

    await page.route("**/api/app/team/users", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: [
            {
              member_id: "team-member-e2e-07",
              name: "analyst@ontrackchain.local",
              email: "analyst@ontrackchain.local",
              role: "ANALYST",
              status: "active",
              note: "",
              linked_identity_count: 0,
              last_identity_seen_at: null,
              created_at: "2026-07-06T12:00:00.000Z",
              updated_at: "2026-07-06T12:10:00.000Z"
            }
          ]
        })
      });
    });

    await page.route("**/api/app/team/users/team-member-e2e-07/external-identities", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ data: [] })
      });
    });

    await page.route("**/api/app/team/federated-directory/users?**", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: [
            {
              provider: "keycloak",
              external_subject: "kc-sub-analyst-07",
              email: "analyst@ontrackchain.local",
              username: "analyst",
              organization_id: "org-e2e",
              role_snapshot: "ANALYST",
              enabled: true,
              match_status: "suggested",
              linked_user_id: null,
              linked_user_email: null,
              role_validation_status: "valid",
              warnings: []
            }
          ]
        })
      });
    });

    await page.route("**/api/app/team/federated-directory/suggestions", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          can_link: false,
          match_reason: "already_linked",
          org_match: true,
          email_match: true,
          provider: "keycloak",
          external_subject: "kc-sub-analyst-07",
          candidate_email: "analyst@ontrackchain.local",
          candidate_username: "analyst",
          candidate_org: "org-e2e",
          role_snapshot: "ANALYST",
          role_validation_status: "valid",
          linked_user_id: "another-user",
          linked_user_email: "another@ontrackchain.local",
          warnings: ["candidate_already_linked"]
        })
      });
    });

    await page.goto("/team");
    await page.getByRole("button", { name: "Editar" }).click();
    await page.getByTestId("team-federated-search-input").fill("analyst");
    await page.getByTestId("team-federated-search-button").click();
    await page.getByTestId("team-federated-link-button").click();

    await expect(
      page.getByText(
        "Sugestão recusada: identidade já vinculada a outro usuário local. Alerta principal: Identidade já vinculada a outro usuário local."
      )
    ).toBeVisible();
    await expect(page.getByText("already_linked")).toHaveCount(0);
    await expect(page.getByText("candidate_already_linked")).toHaveCount(0);
  });

  test("permite filtrar rapidamente candidatos prontos e em revisão manual no diretório federado", async ({ page }) => {
    await seedFrontendAuth(page);

    await page.route("**/api/app/team/users", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: [
            {
              member_id: "team-member-e2e-08",
              name: "analyst@ontrackchain.local",
              email: "analyst@ontrackchain.local",
              role: "ANALYST",
              status: "active",
              note: "",
              linked_identity_count: 0,
              last_identity_seen_at: null,
              created_at: "2026-07-06T12:00:00.000Z",
              updated_at: "2026-07-06T12:10:00.000Z"
            }
          ]
        })
      });
    });

    await page.route("**/api/app/team/users/team-member-e2e-08/external-identities", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ data: [] })
      });
    });

    await page.route("**/api/app/team/federated-directory/users?**", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: [
            {
              provider: "keycloak",
              external_subject: "kc-sub-analyst-ready",
              email: "analyst@ontrackchain.local",
              username: "analyst",
              organization_id: "org-e2e",
              role_snapshot: "ANALYST",
              enabled: true,
              match_status: "suggested",
              linked_user_id: null,
              linked_user_email: null,
              role_validation_status: "valid",
              warnings: []
            },
            {
              provider: "keycloak",
              external_subject: "kc-sub-analyst-review",
              email: "other@external.local",
              username: "review-analyst",
              organization_id: "foreign-org",
              role_snapshot: null,
              enabled: true,
              match_status: "org_match_only",
              linked_user_id: null,
              linked_user_email: null,
              role_validation_status: "missing",
              warnings: ["candidate_org_mismatch", "candidate_role_missing"]
            }
          ]
        })
      });
    });

    await page.goto("/team");
    await page.getByRole("button", { name: "Editar" }).click();
    await page.getByTestId("team-federated-search-input").fill("analyst");
    await page.getByTestId("team-federated-search-button").click();

    await expect(page.getByTestId("team-federated-summary-total")).toContainText("2");
    await expect(page.getByTestId("team-federated-summary-ready")).toContainText("1");
    await expect(page.getByTestId("team-federated-summary-review")).toContainText("1");
    await expect(page.locator('[data-testid="team-federated-result-row"]')).toHaveCount(2);

    await page.getByTestId("team-federated-filter-ready").click();
    await expect(page.locator('[data-testid="team-federated-result-row"]')).toHaveCount(1);
    await expect(page.getByText("kc-sub-analyst-ready")).toBeVisible();
    await expect(page.getByText("kc-sub-analyst-review")).toHaveCount(0);

    await page.getByTestId("team-federated-filter-review").click();
    await expect(page.locator('[data-testid="team-federated-result-row"]')).toHaveCount(1);
    await expect(page.getByText("kc-sub-analyst-review")).toBeVisible();
    await expect(page.getByText("kc-sub-analyst-ready")).toHaveCount(0);

    await page.getByTestId("team-federated-filter-linked").click();
    await expect(page.getByText("Nenhum candidato corresponde ao filtro selecionado.")).toBeVisible();

    await page.getByTestId("team-federated-filter-all").click();
    await expect(page.locator('[data-testid="team-federated-result-row"]')).toHaveCount(2);
  });

  test("ordena candidatos do diretório federado por prioridade operacional", async ({ page }) => {
    await seedFrontendAuth(page);

    await page.route("**/api/app/team/users", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: [
            {
              member_id: "team-member-e2e-09",
              name: "analyst@ontrackchain.local",
              email: "analyst@ontrackchain.local",
              role: "ANALYST",
              status: "active",
              note: "",
              linked_identity_count: 0,
              last_identity_seen_at: null,
              created_at: "2026-07-06T12:00:00.000Z",
              updated_at: "2026-07-06T12:10:00.000Z"
            }
          ]
        })
      });
    });

    await page.route("**/api/app/team/users/team-member-e2e-09/external-identities", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ data: [] })
      });
    });

    await page.route("**/api/app/team/federated-directory/users?**", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: [
            {
              provider: "keycloak",
              external_subject: "kc-sub-linked",
              email: "linked@ontrackchain.local",
              username: "linked-analyst",
              organization_id: "org-e2e",
              role_snapshot: "ANALYST",
              enabled: true,
              match_status: "linked",
              linked_user_id: "local-user-1",
              linked_user_email: "linked@ontrackchain.local",
              role_validation_status: "valid",
              warnings: ["candidate_already_linked_to_member"]
            },
            {
              provider: "keycloak",
              external_subject: "kc-sub-review",
              email: "review@external.local",
              username: "review-analyst",
              organization_id: "foreign-org",
              role_snapshot: null,
              enabled: true,
              match_status: "org_match_only",
              linked_user_id: null,
              linked_user_email: null,
              role_validation_status: "missing",
              warnings: ["candidate_org_mismatch", "candidate_role_missing"]
            },
            {
              provider: "keycloak",
              external_subject: "kc-sub-ready",
              email: "analyst@ontrackchain.local",
              username: "ready-analyst",
              organization_id: "org-e2e",
              role_snapshot: "ANALYST",
              enabled: true,
              match_status: "suggested",
              linked_user_id: null,
              linked_user_email: null,
              role_validation_status: "valid",
              warnings: []
            }
          ]
        })
      });
    });

    await page.goto("/team");
    await page.getByRole("button", { name: "Editar" }).click();
    await page.getByTestId("team-federated-search-input").fill("analyst");
    await page.getByTestId("team-federated-search-button").click();

    const rows = page.locator('[data-testid="team-federated-result-row"]');
    await expect(rows).toHaveCount(3);
    await expect(rows.nth(0)).toContainText("kc-sub-ready");
    await expect(rows.nth(1)).toContainText("kc-sub-review");
    await expect(rows.nth(2)).toContainText("kc-sub-linked");
  });

  test("permite alternar entre prioridade operacional e ordem alfabética no diretório federado", async ({ page }) => {
    await seedFrontendAuth(page);

    await page.route("**/api/app/team/users", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: [
            {
              member_id: "team-member-e2e-10",
              name: "analyst@ontrackchain.local",
              email: "analyst@ontrackchain.local",
              role: "ANALYST",
              status: "active",
              note: "",
              linked_identity_count: 0,
              last_identity_seen_at: null,
              created_at: "2026-07-06T12:00:00.000Z",
              updated_at: "2026-07-06T12:10:00.000Z"
            }
          ]
        })
      });
    });

    await page.route("**/api/app/team/users/team-member-e2e-10/external-identities", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ data: [] })
      });
    });

    await page.route("**/api/app/team/federated-directory/users?**", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: [
            {
              provider: "keycloak",
              external_subject: "kc-sub-linked",
              email: "b-linked@ontrackchain.local",
              username: "linked-analyst",
              organization_id: "org-e2e",
              role_snapshot: "ANALYST",
              enabled: true,
              match_status: "linked",
              linked_user_id: "local-user-1",
              linked_user_email: "b-linked@ontrackchain.local",
              role_validation_status: "valid",
              warnings: ["candidate_already_linked_to_member"]
            },
            {
              provider: "keycloak",
              external_subject: "kc-sub-review",
              email: "m-review@external.local",
              username: "review-analyst",
              organization_id: "foreign-org",
              role_snapshot: null,
              enabled: true,
              match_status: "org_match_only",
              linked_user_id: null,
              linked_user_email: null,
              role_validation_status: "missing",
              warnings: ["candidate_org_mismatch", "candidate_role_missing"]
            },
            {
              provider: "keycloak",
              external_subject: "kc-sub-ready",
              email: "a-ready@ontrackchain.local",
              username: "ready-analyst",
              organization_id: "org-e2e",
              role_snapshot: "ANALYST",
              enabled: true,
              match_status: "suggested",
              linked_user_id: null,
              linked_user_email: null,
              role_validation_status: "valid",
              warnings: []
            }
          ]
        })
      });
    });

    await page.goto("/team");
    await page.getByRole("button", { name: "Editar" }).click();
    await page.getByTestId("team-federated-search-input").fill("analyst");
    await page.getByTestId("team-federated-search-button").click();

    const rows = page.locator('[data-testid="team-federated-result-row"]');
    await expect(rows).toHaveCount(3);
    await expect(rows.nth(0)).toContainText("kc-sub-ready");
    await expect(rows.nth(1)).toContainText("kc-sub-review");
    await expect(rows.nth(2)).toContainText("kc-sub-linked");

    await page.getByTestId("team-federated-sort-alphabetical").click();
    await expect(rows.nth(0)).toContainText("kc-sub-ready");
    await expect(rows.nth(1)).toContainText("kc-sub-linked");
    await expect(rows.nth(2)).toContainText("kc-sub-review");

    await page.getByTestId("team-federated-sort-priority").click();
    await expect(rows.nth(0)).toContainText("kc-sub-ready");
    await expect(rows.nth(1)).toContainText("kc-sub-review");
    await expect(rows.nth(2)).toContainText("kc-sub-linked");
  });

  test("carrega e atualiza preferências locais de filtro e ordenação do diretório federado", async ({ page }) => {
    await seedFrontendAuth(page);

    await page.addInitScript(() => {
      window.localStorage.setItem("otc-team-federated-filter", "all");
      window.localStorage.setItem("otc-team-federated-sort", "alphabetical");
      window.localStorage.setItem("otc-team-federated-query", "persisted-analyst");
    });

    await page.route("**/api/app/team/users", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: [
            {
              member_id: "team-member-e2e-11",
              name: "analyst@ontrackchain.local",
              email: "analyst@ontrackchain.local",
              role: "ANALYST",
              status: "active",
              note: "",
              linked_identity_count: 0,
              last_identity_seen_at: null,
              created_at: "2026-07-06T12:00:00.000Z",
              updated_at: "2026-07-06T12:10:00.000Z"
            }
          ]
        })
      });
    });

    await page.route("**/api/app/team/users/team-member-e2e-11/external-identities", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ data: [] })
      });
    });

    await page.route("**/api/app/team/federated-directory/users?**", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: [
            {
              provider: "keycloak",
              external_subject: "kc-sub-linked",
              email: "b-linked@ontrackchain.local",
              username: "linked-analyst",
              organization_id: "org-e2e",
              role_snapshot: "ANALYST",
              enabled: true,
              match_status: "linked",
              linked_user_id: "local-user-1",
              linked_user_email: "b-linked@ontrackchain.local",
              role_validation_status: "valid",
              warnings: ["candidate_already_linked_to_member"]
            },
            {
              provider: "keycloak",
              external_subject: "kc-sub-review",
              email: "m-review@external.local",
              username: "review-analyst",
              organization_id: "foreign-org",
              role_snapshot: null,
              enabled: true,
              match_status: "org_match_only",
              linked_user_id: null,
              linked_user_email: null,
              role_validation_status: "missing",
              warnings: ["candidate_org_mismatch", "candidate_role_missing"]
            },
            {
              provider: "keycloak",
              external_subject: "kc-sub-ready",
              email: "a-ready@ontrackchain.local",
              username: "ready-analyst",
              organization_id: "org-e2e",
              role_snapshot: "ANALYST",
              enabled: true,
              match_status: "suggested",
              linked_user_id: null,
              linked_user_email: null,
              role_validation_status: "valid",
              warnings: []
            }
          ]
        })
      });
    });

    await page.goto("/team");
    await page.getByRole("button", { name: "Editar" }).click();
    await expect(page.getByTestId("team-federated-context-notice")).toContainText("Contexto anterior da triagem restaurado.");
    await expect(page.getByTestId("team-federated-search-input")).toHaveValue("persisted-analyst");
    await page.getByTestId("team-federated-search-input").fill("analyst");
    await page.getByTestId("team-federated-search-button").click();

    const rows = page.locator('[data-testid="team-federated-result-row"]');
    await expect(page.getByTestId("team-federated-sort-alphabetical")).toHaveClass(/otc-button--accent/);
    await expect(rows).toHaveCount(3);
    await expect(rows.nth(0)).toContainText("kc-sub-ready");
    await expect(rows.nth(1)).toContainText("kc-sub-linked");
    await expect(rows.nth(2)).toContainText("kc-sub-review");

    await page.getByTestId("team-federated-filter-review").click();
    await page.getByTestId("team-federated-sort-priority").click();
    await expect(rows).toHaveCount(1);
    await expect(rows.nth(0)).toContainText("kc-sub-review");

    const persistedPreferences = await page.evaluate(() => ({
      filter: window.localStorage.getItem("otc-team-federated-filter"),
      sort: window.localStorage.getItem("otc-team-federated-sort"),
      query: window.localStorage.getItem("otc-team-federated-query")
    }));

    expect(persistedPreferences).toEqual({
      filter: "review",
      sort: "priority",
      query: "analyst"
    });

    await expect(page.getByTestId("team-federated-clear-context-button")).toHaveAttribute(
      "title",
      "Limpa busca e resultados carregados; pedirá confirmação."
    );
    await page.getByTestId("team-federated-clear-context-button").click();
    await expect(page.getByTestId("team-confirm-dialog-clear-context")).toBeVisible();
    await expect(page.getByTestId("team-confirm-dialog-clear-context")).toContainText("Confirmar limpeza da triagem");
    await expect(page.getByTestId("team-confirm-dialog-clear-context")).toContainText(
      "Há 3 candidato(s) carregado(s) na triagem federada."
    );
    await page.getByTestId("team-confirm-dialog-clear-context-confirm").click();
    await expect(page.getByTestId("team-federated-context-notice")).toContainText("Contexto da triagem limpo com sucesso.");
    await expect(page.getByTestId("team-federated-search-input")).toHaveValue("");
    await expect(page.getByTestId("team-federated-search-button")).toBeDisabled();
    await expect(page.getByText("Nenhum candidato retornado pelo IdP ainda.")).toBeVisible();
    await expect(page.getByTestId("team-federated-filter-bar")).toHaveCount(0);
    await expect(page.getByTestId("team-federated-sort-bar")).toHaveCount(0);

    const clearedPreferences = await page.evaluate(() => ({
      filter: window.localStorage.getItem("otc-team-federated-filter"),
      sort: window.localStorage.getItem("otc-team-federated-sort"),
      query: window.localStorage.getItem("otc-team-federated-query")
    }));

    expect(clearedPreferences).toEqual({
      filter: "all",
      sort: "priority",
      query: ""
    });
  });

  test("bloqueia busca assistida vazia ou só com espaços antes de chamar o IdP", async ({ page }) => {
    await seedFrontendAuth(page);

    let federatedSearchCalls = 0;

    await page.route("**/api/app/team/users", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: [
            {
              member_id: "team-member-e2e-12",
              name: "analyst@ontrackchain.local",
              email: "analyst@ontrackchain.local",
              role: "ANALYST",
              status: "active",
              note: "",
              linked_identity_count: 0,
              last_identity_seen_at: null,
              created_at: "2026-07-06T12:00:00.000Z",
              updated_at: "2026-07-06T12:10:00.000Z"
            }
          ]
        })
      });
    });

    await page.route("**/api/app/team/users/team-member-e2e-12/external-identities", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ data: [] })
      });
    });

    await page.route("**/api/app/team/federated-directory/users?**", async (route: Route) => {
      federatedSearchCalls += 1;
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ data: [] })
      });
    });

    await page.goto("/team");
    await page.getByRole("button", { name: "Editar" }).click();

    await expect(page.getByTestId("team-federated-search-hint")).toContainText(
      "Digite email, username ou parte do identificador para buscar candidatos no IdP."
    );
    await expect(page.getByTestId("team-federated-search-button")).toBeDisabled();
    await page.getByTestId("team-federated-search-input").fill("   ");
    await expect(page.getByTestId("team-federated-search-button")).toBeDisabled();
    await page.getByTestId("team-federated-search-form").evaluate((form: HTMLFormElement) => form.requestSubmit());
    await expect(page.getByText("Informe email, username ou parte do identificador antes de buscar.")).toBeVisible();
    expect(federatedSearchCalls).toBe(0);
  });

  test("mantém o contexto federado intacto quando o operador cancela a limpeza", async ({ page }) => {
    await seedFrontendAuth(page);

    await page.addInitScript(() => {
      window.localStorage.setItem("otc-team-federated-filter", "all");
      window.localStorage.setItem("otc-team-federated-sort", "alphabetical");
      window.localStorage.setItem("otc-team-federated-query", "persisted-analyst");
    });

    await page.route("**/api/app/team/users", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: [
            {
              member_id: "team-member-e2e-13",
              name: "analyst@ontrackchain.local",
              email: "analyst@ontrackchain.local",
              role: "ANALYST",
              status: "active",
              note: "",
              linked_identity_count: 0,
              last_identity_seen_at: null,
              created_at: "2026-07-06T12:00:00.000Z",
              updated_at: "2026-07-06T12:10:00.000Z"
            }
          ]
        })
      });
    });

    await page.route("**/api/app/team/users/team-member-e2e-13/external-identities", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ data: [] })
      });
    });

    await page.route("**/api/app/team/federated-directory/users?**", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: [
            {
              provider: "keycloak",
              external_subject: "kc-sub-ready",
              email: "analyst@idp.local",
              username: "analyst.idp",
              organization_id: "org-e2e",
              role_snapshot: "ANALYST",
              enabled: true,
              match_status: "suggested",
              linked_user_id: null,
              linked_user_email: null,
              role_validation_status: "role_match",
              warnings: []
            },
            {
              provider: "keycloak",
              external_subject: "kc-sub-review",
              email: "review@idp.local",
              username: "review.idp",
              organization_id: "org-other",
              role_snapshot: "VIEWER",
              enabled: true,
              match_status: "org_match_only",
              linked_user_id: null,
              linked_user_email: null,
              role_validation_status: "role_mismatch",
              warnings: ["candidate_org_mismatch", "candidate_role_mismatch"]
            },
            {
              provider: "keycloak",
              external_subject: "kc-sub-linked",
              email: "linked@idp.local",
              username: "linked.idp",
              organization_id: "org-e2e",
              role_snapshot: "ANALYST",
              enabled: true,
              match_status: "linked",
              linked_user_id: "team-member-existing",
              linked_user_email: "linked@ontrackchain.local",
              role_validation_status: "role_match",
              warnings: []
            }
          ]
        })
      });
    });

    await page.goto("/team");
    await page.getByRole("button", { name: "Editar" }).click();
    await page.getByTestId("team-federated-search-input").fill("analyst");
    await page.getByTestId("team-federated-search-button").click();

    const rows = page.locator('[data-testid="team-federated-result-row"]');
    await expect(rows).toHaveCount(3);

    await page.getByTestId("team-federated-clear-context-button").click();
    await expect(page.getByTestId("team-confirm-dialog-clear-context")).toBeVisible();
    await page.getByTestId("team-confirm-dialog-clear-context-cancel").click();

    await expect(page.getByTestId("team-federated-search-input")).toHaveValue("analyst");
    await expect(rows).toHaveCount(3);
    await expect(page.getByTestId("team-federated-context-notice")).toHaveCount(0);
    await expect(page.getByTestId("team-federated-filter-bar")).toHaveCount(1);
    await expect(page.getByTestId("team-federated-sort-bar")).toHaveCount(1);

    const persistedPreferences = await page.evaluate(() => ({
      filter: window.localStorage.getItem("otc-team-federated-filter"),
      sort: window.localStorage.getItem("otc-team-federated-sort"),
      query: window.localStorage.getItem("otc-team-federated-query")
    }));

    expect(persistedPreferences).toEqual({
      filter: "all",
      sort: "alphabetical",
      query: "analyst"
    });
  });

  test("limpa contexto local sem diálogo quando ainda não há resultados carregados", async ({ page }) => {
    await seedFrontendAuth(page);

    await page.addInitScript(() => {
      window.localStorage.setItem("otc-team-federated-filter", "review");
      window.localStorage.setItem("otc-team-federated-sort", "priority");
      window.localStorage.setItem("otc-team-federated-query", "persisted-review");
    });

    await page.route("**/api/app/team/users", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: [
            {
              member_id: "team-member-e2e-14",
              name: "reviewer@ontrackchain.local",
              email: "reviewer@ontrackchain.local",
              role: "REVIEWER",
              status: "active",
              note: "",
              linked_identity_count: 0,
              last_identity_seen_at: null,
              created_at: "2026-07-06T12:00:00.000Z",
              updated_at: "2026-07-06T12:10:00.000Z"
            }
          ]
        })
      });
    });

    await page.route("**/api/app/team/users/team-member-e2e-14/external-identities", async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ data: [] })
      });
    });

    await page.goto("/team");
    await page.getByRole("button", { name: "Editar" }).click();

    await expect(page.getByTestId("team-federated-context-notice")).toContainText("Contexto anterior da triagem restaurado.");
    await expect(page.getByTestId("team-federated-search-input")).toHaveValue("persisted-review");
    await expect(page.getByTestId("team-federated-clear-context-button")).toHaveAttribute(
      "title",
      "Limpa busca, filtros e ordenação locais."
    );

    await page.getByTestId("team-federated-clear-context-button").click();

    await expect(page.getByTestId("team-confirm-dialog-clear-context")).toHaveCount(0);
    await expect(page.getByTestId("team-federated-context-notice")).toContainText("Contexto da triagem limpo com sucesso.");
    await expect(page.getByTestId("team-federated-search-input")).toHaveValue("");
    await expect(page.getByTestId("team-federated-search-button")).toBeDisabled();

    const clearedPreferences = await page.evaluate(() => ({
      filter: window.localStorage.getItem("otc-team-federated-filter"),
      sort: window.localStorage.getItem("otc-team-federated-sort"),
      query: window.localStorage.getItem("otc-team-federated-query")
    }));

    expect(clearedPreferences).toEqual({
      filter: "all",
      sort: "priority",
      query: ""
    });
  });
});
