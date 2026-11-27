import { housesApi } from "../../api/houses";
import { FormModal } from "../../components/Modal";
import { houseLoginField, passwordFields } from "../../components/Fields";
export function HouseAccessModal({
  mode,
  login,
  onClose,
  onSuccess,
}: {
  mode: "create" | "join";
  login?: string;
  onClose: () => void;
  onSuccess: (id: string) => void;
}) {
  const create = mode === "create";
  return (
    <FormModal
      title={create ? "Новый дом" : "Присоединиться к дому"}
      description={
        create
          ? "Создайте пространство для тех, кто рядом. Вы станете его администратором."
          : "Попросите идентификатор и пароль у администратора дома."
      }
      fields={[
        ...(create
          ? [
              {
                name: "name",
                label: "Название дома",
                maxLength: 100,
                autoComplete: "off",
              },
            ]
          : []),
        { ...houseLoginField, defaultValue: login },
        ...(create
          ? passwordFields()
          : [
              {
                name: "password",
                label: "Пароль дома",
                type: "password",
                autoComplete: "off",
                maxLength: 128,
              },
            ]),
      ]}
      submitLabel={create ? "Создать дом" : "Присоединиться"}
      onClose={onClose}
      onSubmit={async (data) => {
        const result = create
          ? await housesApi.create(data)
          : await housesApi.join(data);
        onSuccess("house_id" in result ? result.house_id : result.id);
      }}
    />
  );
}
