import { AppLayout } from "@/components/app-layout"
import { ChartAreaInteractive } from "@/components/chart-area-interactive"
import { DataTable } from "@/components/data-table"
import { SectionCards } from "@/components/section-cards"

import data from "../app/dashboard/data.json"

export default function DemoDashboard() {
  return (
    <AppLayout pageTitle="Demo Dashboard" sidebarVariant="inset">
      <div className="flex flex-col gap-4 py-4 md:gap-6 md:py-6">
        <SectionCards />
        <div className="px-4 lg:px-6">
          <ChartAreaInteractive />
        </div>
        <DataTable data={data} />
      </div>
    </AppLayout>
  )
}
